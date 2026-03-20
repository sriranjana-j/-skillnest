from io import BytesIO

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Max
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from xhtml2pdf import pisa

from modules.interview_ai import analyze_answer, summarize_interview
from modules.loader import load_questions
from modules.randomizer import pick_random_questions
from modules.resume_engine import generate_pdf_resume
from modules.score import evaluate_score
from modules.tips import improvement_tips
from .models import InterviewScore, Progress


INTERVIEW_QUESTIONS = [
	"Tell me about yourself.",
	"What are your technical strengths?",
	"What is your biggest technical weakness?",
	"Explain one of your projects.",
	"Why should we hire you?",
]


def _clear_interview_session(session):
	for key in [
		"q_index",
		"chat",
		"score",
		"improvements",
		"last_answer",
		"question_feedback",
		"interview_max_score",
		"overall_summary",
		"ai_status",
	]:
		session.pop(key, None)


@require_GET
def home(request):
	if request.user.is_authenticated:
		return redirect("dashboard")
	return render(request, "login.html")


@login_required(login_url="home")
@require_GET
def dashboard(request):
	agg = Progress.objects.filter(user=request.user).aggregate(
		total=Count("id"),
		best=Max("score"),
		avg=Avg("score"),
	)
	stats = {
		"total": agg["total"] or 0,
		"best": agg["best"] or 0,
		"avg": round(agg["avg"] or 0, 2),
	}
	return render(request, "dashboard.html", {"user": request.user.username, "stats": stats})


@require_POST
def login_view(request):
	username = request.POST.get("username", "").strip()
	password = request.POST.get("password", "")
	user = authenticate(request, username=username, password=password)

	if user is None:
		messages.error(request, "Invalid login credentials.")
		return redirect("home")

	login(request, user)
	return redirect("dashboard")


@require_POST
def register_view(request):
	username = request.POST.get("username", "").strip()
	password = request.POST.get("password", "")

	if not username or not password:
		messages.error(request, "Username and password are required.")
		return redirect("home")

	if User.objects.filter(username=username).exists():
		messages.error(request, "Username already exists.")
		return redirect("home")

	user = User.objects.create_user(username=username, password=password)
	login(request, user)
	return redirect("dashboard")


@require_GET
def logout_view(request):
	logout(request)
	request.session.flush()
	return redirect("home")


@login_required(login_url="home")
@require_GET
def domain(request):
	context = {
		"domains": ["aptitude", "technical", "hr", "ai", "ml", "datasci", "software", "logical"],
		"counts": [20, 40, 60, 100, 150],
	}
	return render(request, "domain.html", context)


@login_required(login_url="home")
@require_GET
def quiz(request, domain, count):
	try:
		questions = load_questions(domain)
	except FileNotFoundError:
		messages.error(request, f"Question bank for domain '{domain}' was not found.")
		return redirect("domain")

	try:
		requested_count = int(count)
	except (TypeError, ValueError):
		messages.error(request, "Invalid question count selected.")
		return redirect("domain")

	if requested_count <= 0:
		messages.error(request, "Question count must be greater than zero.")
		return redirect("domain")

	if not isinstance(questions, list) or not questions:
		messages.error(request, "No questions available for this domain.")
		return redirect("domain")

	selected = pick_random_questions(questions, requested_count)
	request.session["current_quiz"] = selected
	request.session["quiz_domain"] = domain
	request.session["quiz_total"] = requested_count
	return render(request, "quiz.html", {"questions": selected, "domain": domain, "count": requested_count})


@login_required(login_url="home")
@require_POST
def submit_quiz(request):
	current_quiz = request.session.get("current_quiz", [])
	quiz_domain = request.session.get("quiz_domain", "unknown")
	quiz_total = request.session.get("quiz_total", 0)

	score, wrong = evaluate_score(current_quiz, request.POST)
	tips = improvement_tips(wrong)

	Progress.objects.create(
		user=request.user,
		domain=quiz_domain,
		score=score,
		total=quiz_total,
	)

	return render(request, "result.html", {"score": score, "tips": tips})


@login_required(login_url="home")
def interview(request):
	if request.method == "GET" and request.GET.get("reset"):
		_clear_interview_session(request.session)
		return redirect("interview")

	if "q_index" not in request.session or request.session.get("q_index") is None:
		request.session["q_index"] = 0
		request.session["chat"] = []
		request.session["score"] = 0
		request.session["improvements"] = []
		request.session["question_feedback"] = []
		request.session["interview_max_score"] = len(INTERVIEW_QUESTIONS) * 15
		request.session["ai_status"] = "Waiting"

	q_index = request.session.get("q_index", 0)
	if q_index >= len(INTERVIEW_QUESTIONS):
		return redirect("interview_finish")

	if request.method == "POST":
		action = request.POST.get("interview_action", "send").strip().lower()
		if action == "restart":
			_clear_interview_session(request.session)
			messages.info(request, "Interview restarted from Question 1.")
			return redirect("interview")
		if action == "stop":
			_clear_interview_session(request.session)
			messages.info(request, "Interview stopped.")
			return redirect("dashboard")

		chat = request.session.get("chat", [])
		current_question = INTERVIEW_QUESTIONS[q_index]
		timed_out = request.POST.get("timed_out") == "1"
		answer = request.POST.get("answer", "").strip()

		if timed_out and not answer:
			chat.append(["Bot", "⏳ Time up for this question. Moving to the next one. Tip: keep answers in STAR format with measurable impact."])
			request.session["chat"] = chat
			improvements = request.session.get("improvements", [])
			improvements.append(
				f"Q{q_index + 1}: Time ran out. Next time answer with 3 to 5 STAR lines and end with a measurable impact."
			)
			request.session["improvements"] = improvements
			feedback = request.session.get("question_feedback", [])
			feedback.append(
				{
					"question": current_question,
					"score": 0,
					"quality": "Needs Improvement",
					"strengths": ["You stayed in the interview flow."],
					"improvements": ["Answer timed out before technical details were shared."],
					"suggestion": "Respond faster with STAR and include at least one action and one result.",
					"improved_sample_answer": "I handled a production issue by identifying root cause, implementing a fix, and verifying improvement with metrics.",
				}
			)
			request.session["question_feedback"] = feedback
			request.session["q_index"] = request.session.get("q_index", 0) + 1
			request.session["ai_status"] = "Local AI"
			return redirect("interview")

		if answer:
			result = analyze_answer(answer, request.session.get("last_answer"), current_question)
			request.session["ai_status"] = result.get("feedback_source", "Local AI")
			chat.append(["You", answer])
			chat.append(["Bot", result["reply"]])
			request.session["chat"] = chat

			improvements = request.session.get("improvements", [])
			suggestion = result.get("improvement_suggestion")
			if suggestion:
				improvements.append(f"Q{q_index + 1}: {suggestion}")
			request.session["improvements"] = improvements

			request.session["last_answer"] = result.get("normalized_answer", answer.lower())
			request.session["score"] = request.session.get("score", 0) + int(result.get("score", 0))
			feedback = request.session.get("question_feedback", [])
			feedback.append(
				{
					"question": current_question,
					"score": int(result.get("score", 0)),
					"quality": result.get("quality", "Developing"),
					"strengths": result.get("strengths", []),
					"improvements": result.get("improvements", []),
					"suggestion": suggestion or "Add more technical depth and measurable impact.",
					"improved_sample_answer": result.get("improved_sample_answer", ""),
				}
			)
			request.session["question_feedback"] = feedback
			request.session["q_index"] = request.session.get("q_index", 0) + 1

		return redirect("interview")

	question = INTERVIEW_QUESTIONS[q_index]
	question_number = q_index + 1
	question_total = len(INTERVIEW_QUESTIONS)
	context = {
		"question": question,
		"chat": request.session.get("chat", []),
		"timer": 90,
		"question_number": question_number,
		"question_total": question_total,
		"progress_pct": int((question_number - 1) * 100 / question_total),
		"ai_status": request.session.get("ai_status", "Local AI"),
	}
	return render(request, "interview.html", context)


@login_required(login_url="home")
@require_GET
def interview_finish(request):
	if "score" not in request.session:
		return redirect("interview")

	final_score = int(request.session.get("score", 0))
	improvements = request.session.get("improvements", [])
	question_feedback = request.session.get("question_feedback", [])
	max_score = int(request.session.get("interview_max_score", len(INTERVIEW_QUESTIONS) * 15))
	overall_summary = summarize_interview(question_feedback)

	InterviewScore.objects.create(user=request.user, score=final_score)

	_clear_interview_session(request.session)

	return render(
		request,
		"interview_finish.html",
		{
			"score": final_score,
			"max_score": max_score,
			"user": request.user.username,
			"improvements": improvements,
			"question_feedback": question_feedback,
			"overall_summary": overall_summary,
		},
	)


@login_required(login_url="home")
@require_GET
def download_interview_report(request):
	latest_score = InterviewScore.objects.filter(user=request.user).first()
	if latest_score is None:
		messages.error(request, "No interview report found yet.")
		return redirect("interview")

	score = int(latest_score.score)
	html = render_to_string("report_template.html", {"user": request.user.username, "score": score})

	pdf = BytesIO()
	pisa.CreatePDF(html, dest=pdf)
	pdf.seek(0)

	response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
	response["Content-Disposition"] = f'attachment; filename="{request.user.username}_interview_report.pdf"'
	return response


@login_required(login_url="home")
def resume(request):
	if request.method == "POST":
		data = request.POST.dict()
		request.session["resume_data"] = data
		return render(request, "resume_preview.html", {"data": data})
	return render(request, "resume.html")


@login_required(login_url="home")
@require_GET
def download_pdf(request):
	resume_data = request.session.get("resume_data", {})
	if not resume_data:
		messages.error(request, "Create a resume preview first.")
		return redirect("resume")

	file_path = generate_pdf_resume(resume_data, None, "simple")
	with open(file_path, "rb") as fh:
		pdf_data = fh.read()

	response = HttpResponse(pdf_data, content_type="application/pdf")
	response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
	return response


@login_required(login_url="home")
@require_GET
def progress(request):
	rows = Progress.objects.filter(user=request.user).values_list("domain", "score", "total", "date")
	return render(request, "progress.html", {"data": list(rows), "user": request.user.username})
