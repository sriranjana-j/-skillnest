# Skill Nest

Skill Nest is a web-based application developed using Django that helps users practice aptitude questions and prepare for interviews through a simple interface.

The main focus of the system is aptitude practice, with additional features like a basic interview chatbot and resume generation.

---

## 🚀 Features

### 1. Aptitude Practice (Main Module)
- Displays aptitude questions
- Multiple choice answers
- Calculates score after submission
- Shows result to the user

### 2. Interview Chat (Secondary Feature)
- Text-based interview questions
- User inputs answers
- System gives feedback using simple keyword matching
- No machine learning used (rule-based logic only)

### 3. Resume Builder
- Users can enter details
- Generates a downloadable PDF resume

### 4. User System
- Login and registration
- Tracks user activity (basic)

---

## 🛠️ Tech Stack

- Backend: Django (Python)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- PDF Generation: xhtml2pdf

---

## ⚙️ How It Works

1. User logs in
2. Selects module:
   - Aptitude Test
   - Interview Chat
3. System processes input
4. Displays score or feedback

---

## 🧠 Logic Used

- Aptitude:
  - Direct answer matching for scoring

- Interview Chat:
  - Keyword-based evaluation
  - STAR-related word detection (basic)
  - Random fallback suggestions

---

## ⚠️ Limitations

- Aptitude questions are static
- No adaptive difficulty
- Interview chatbot uses only keyword matching
- No real AI or NLP models
- Feedback may not always be accurate

---

## 🔮 Future Improvements

- Add dynamic question generation
- Improve answer evaluation logic
- Add AI-based analysis
- Enhance UI and reporting system

---

## 📌 Conclusion

Skill Nest provides a simple platform for practicing aptitude questions and basic interview preparation. It is designed mainly for beginners and can be improved further with advanced features.
------------
