def improvement_tips(keywords):
    tips = []
    unique = set(keywords)

    for key in unique:
        key = key.strip()
        if key:
            tips.append(f"Improve concepts in: {key}")
    
    return tips
