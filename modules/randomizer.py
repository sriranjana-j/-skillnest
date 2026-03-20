import random

def pick_random_questions(questions, count):
    random.shuffle(questions)
    return questions[:count]
