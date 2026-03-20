import re


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(p in text for p in patterns)


def _score_to_quality(average_score: float) -> str:
    if average_score < 4.5:
        return "Needs Improvement"
    if average_score < 6.5:
        return "Developing"
    if average_score < 8.5:
        return "Strong"
    return "Excellent"


def _fallback_feedback(question: str, answer: str, repeated_flag: bool) -> dict:
    text = (answer or "").strip()
    normalized = text.lower()
    words = _tokenize(normalized)
    word_count = len(words)

    has_number = bool(re.search(r"\d|%", text))
    has_action = _contains_any(
        normalized,
        [
            "built", "created", "implemented", "designed", "led", "managed", "optimized",
            "improved", "resolved", "developed", "integrated", "automated",
        ],
    )
    has_result = _contains_any(normalized, ["result", "impact", "improved", "reduced", "increased", "%", "saved"])
    has_structure = _contains_any(normalized, ["first", "then", "finally", "because", "therefore", "so that"])

    clarity = min(10, 3 + (2 if word_count >= 12 else 0) + (2 if has_structure else 0) + (1 if not repeated_flag else 0))
    relevance = min(10, 5 + (2 if any(w in normalized for w in _tokenize(question)) else 0) + (1 if has_action else 0))
    technical_depth = min(10, 3 + (3 if has_action else 0) + (2 if has_number else 0) + (1 if has_result else 0))
    communication = min(10, 4 + (2 if word_count >= 15 else 0) + (1 if has_structure else 0))
    confidence_structure = min(10, 4 + (2 if "i " in f" {normalized} " else 0) + (1 if has_result else 0))

    strengths: list[str] = []
    improvements: list[str] = []

    if has_action:
        strengths.append("You described actions you took instead of only giving general statements.")
    if has_result:
        strengths.append("You included outcome-oriented language that shows impact.")
    if has_number:
        strengths.append("You used numbers/metrics, which increases credibility.")

    if word_count < 12:
        improvements.append("Your answer is too short for interview depth; expand with context and execution detail.")
    if not has_result:
        improvements.append("You did not clearly state measurable results.")
    if repeated_flag:
        improvements.append("This answer repeats previous wording and feels less authentic.")

    if not strengths:
        strengths.append("You attempted to answer directly and stayed on topic.")

    if not improvements:
        improvements.append("Add one concrete technical detail such as tool, architecture choice, or debugging approach.")

    suggestion = "Use a 3-line STAR style response: context, your exact technical action, and a measurable result."
    if not has_result:
        suggestion = "Add one metric to this answer, such as latency reduced, bugs fixed, or delivery time improved."
    elif word_count < 12:
        suggestion = "Keep your current point, but add what problem existed and why your action worked technically."

    scenario = question.strip() if (question or "").strip() else "a similar technical scenario"
    improved_sample = (
        f"In this scenario ({scenario}), I identified the core issue, implemented a focused technical fix, "
        "and validated it with testing/monitoring; as a result, performance and reliability improved measurably."
    )

    return {
        "criteria": {
            "clarity": clarity,
            "relevance": relevance,
            "technical_depth": technical_depth,
            "communication_quality": communication,
            "confidence_structure": confidence_structure,
        },
        "strengths": strengths[:2],
        "improvements": improvements[:2],
        "suggestion": suggestion,
        "improved_sample_answer": improved_sample,
    }


def analyze_answer(answer, last_answer=None, question=None):
    text = (answer or "").strip()
    normalized = text.lower()
    words = _tokenize(normalized)
    word_count = len(words)

    if word_count < 2:
        suggestion = "Use at least 3 to 5 lines: context, your technical action, and measurable result."
        return {
            "reply": "Answer too short to evaluate deeply. Please provide a fuller response.",
            "score": 0,
            "valid": False,
            "normalized_answer": normalized,
            "quality": "Needs Improvement",
            "missing_parts": ["Situation", "Task", "Action", "Result"],
            "matched_skills": [],
            "word_count": word_count,
            "improvement_suggestion": suggestion,
            "strengths": ["You attempted to answer promptly."],
            "improvements": ["Expand your answer with specific technical details and outcome."],
            "improved_sample_answer": "I handled a technical issue by identifying root cause, applying a fix, and validating results with measurable impact.",
            "criteria": {
                "clarity": 2,
                "relevance": 3,
                "technical_depth": 2,
                "communication_quality": 2,
                "confidence_structure": 2,
            },
        }

    last_answer_normalized = (last_answer or "").strip().lower()
    repeated_flag = bool(last_answer_normalized and normalized == last_answer_normalized)
    feedback = _fallback_feedback(question or "", text, repeated_flag)
    feedback_source = "Local AI"
    groq_error = None

    criteria = feedback["criteria"]
    avg = (
        criteria["clarity"]
        + criteria["relevance"]
        + criteria["technical_depth"]
        + criteria["communication_quality"]
        + criteria["confidence_structure"]
    ) / 5.0

    quality = _score_to_quality(avg)
    score = max(1, min(15, int(round(avg * 1.5))))

    source_label = feedback_source

    reply_lines = [
        f"Answer analysis ({source_label}):",
        "Strengths: " + " | ".join(feedback["strengths"]),
        "Improvements: " + " | ".join(feedback["improvements"]),
        "Suggestion: " + feedback["suggestion"],
        "Improved sample: " + feedback["improved_sample_answer"],
    ]

    return {
        "reply": "\n".join(reply_lines),
        "score": score,
        "valid": True,
        "normalized_answer": normalized,
        "quality": quality,
        "missing_parts": [],
        "matched_skills": [],
        "word_count": word_count,
        "feedback_source": feedback_source,
        "groq_error": groq_error,
        "improvement_suggestion": feedback["suggestion"],
        "strengths": feedback["strengths"],
        "improvements": feedback["improvements"],
        "improved_sample_answer": feedback["improved_sample_answer"],
        "criteria": criteria,
    }


def summarize_interview(question_feedback: list[dict]) -> str:
    if not question_feedback:
        return "Insufficient data for interview summary."

    avg_score = sum(int(item.get("score", 0)) for item in question_feedback) / max(len(question_feedback), 1)
    high = [q for q in question_feedback if int(q.get("score", 0)) >= 10]
    low = [q for q in question_feedback if int(q.get("score", 0)) <= 6]

    summary = [
        f"Average score per question: {avg_score:.1f}/15.",
        f"Strong answers: {len(high)}.",
        f"Answers needing improvement: {len(low)}.",
    ]

    if low:
        summary.append("Main pattern: improve result quantification and answer structure consistency.")
    else:
        summary.append("Main pattern: maintain current quality and sharpen technical depth with concrete tradeoffs.")

    return " ".join(summary)
