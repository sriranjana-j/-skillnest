def evaluate_score(questions, user_answers):
    score = 0
    wrong_keywords = []

    for q in questions:
        qid = str(q["id"])
        correct = q["answer"]
        user_choice = user_answers.get(qid)

        if user_choice == correct:
            score += 1
        else:
            wrong_keywords.append(q.get("keyword", ""))

    return score, wrong_keywords
