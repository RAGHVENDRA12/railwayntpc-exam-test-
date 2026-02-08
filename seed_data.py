from sqlalchemy.orm import Session
import models
import database
import json

def seed_questions(db: Session):
    # Check if questions exist
    if db.query(models.Question).first():
        return

    questions_data = [
        # Maths
        {"subject": "Maths", "topic": "Algebra", "text": "If x + 1/x = 2, find x^100 + 1/x^100.", "options": ["0", "1", "2", "100"], "correct_option": "2", "explanation": "If x + 1/x = 2, then x = 1. So 1^100 + 1/1^100 = 1 + 1 = 2.", "difficulty": "Easy"},
        {"subject": "Maths", "topic": "Percentage", "text": "If A is 20% more than B, B is how much percent less than A?", "options": ["16.66%", "20%", "25%", "33.33%"], "correct_option": "16.66%", "explanation": "Let B=100, A=120. Diff=20. % Less = (20/120)*100 = 16.66%.", "difficulty": "Medium"},
        {"subject": "Maths", "topic": "Trigonometry", "text": "Value of sin(45) + cos(45)?", "options": ["1", "sqrt(2)", "2", "1/sqrt(2)"], "correct_option": "sqrt(2)", "explanation": "1/sqrt(2) + 1/sqrt(2) = 2/sqrt(2) = sqrt(2).", "difficulty": "Easy"},
        {"subject": "Maths", "topic": "Time & Work", "text": "A can do a work in 10 days, B in 15 days. Together?", "options": ["5 days", "6 days", "8 days", "12 days"], "correct_option": "6 days", "explanation": "1/10 + 1/15 = 5/30 = 1/6. So 6 days.", "difficulty": "Medium"},
        {"subject": "Maths", "topic": "Profit Loss", "text": "CP=100, SP=120. Profit %?", "options": ["10%", "20%", "15%", "25%"], "correct_option": "20%", "explanation": "Profit = 20. % = (20/100)*100 = 20%.", "difficulty": "Easy"},
        
        # Reasoning
        {"subject": "Reasoning", "topic": "Analogy", "text": "Virus : Smallpox :: Bacteria : ?", "options": ["Typhoid", "Malaria", "Covid", "Sleeping Sickness"], "correct_option": "Typhoid", "explanation": "Smallpox is caused by Virus, Typhoid by Bacteria.", "difficulty": "Easy"},
        {"subject": "Reasoning", "topic": "Series", "text": "2, 6, 12, 20, 30, ...?", "options": ["40", "42", "44", "48"], "correct_option": "42", "explanation": "+4, +6, +8, +10, +12. 30+12=42.", "difficulty": "Medium"},
        {"subject": "Reasoning", "topic": "Coding", "text": "If CAT = 24, DOG = ?", "options": ["24", "25", "26", "27"], "correct_option": "26", "explanation": "C(3)+A(1)+T(20)=24. D(4)+O(15)+G(7)=26.", "difficulty": "Medium"},
        {"subject": "Reasoning", "topic": "Direction", "text": "A man walks 5km North, turns Right walks 5km. Direction from start?", "options": ["North", "North-East", "East", "South-East"], "correct_option": "North-East", "explanation": "Standard direction diagram.", "difficulty": "Easy"},
        
        # GK
        {"subject": "GK", "topic": "Polity", "text": "Fundamental Rights borrowed from?", "options": ["UK", "USA", "Canada", "Ireland"], "correct_option": "USA", "explanation": "Fundamental Rights are from US Constitution.", "difficulty": "Medium"},
        {"subject": "GK", "topic": "History", "text": "Battle of Plassey fought in?", "options": ["1757", "1764", "1857", "1947"], "correct_option": "1757", "explanation": "1757 between Siraj-ud-Daulah and British.", "difficulty": "Medium"},
        {"subject": "GK", "topic": "Geography", "text": "Longest river in India?", "options": ["Ganga", "Yamuna", "Godavari", "Brahmaputra"], "correct_option": "Ganga", "explanation": "Ganga is the longest river entirely in India.", "difficulty": "Easy"},
        
        # Science
        {"subject": "Science", "topic": "Physics", "text": "Unit of Force?", "options": ["Joule", "Newton", "Watt", "Pascal"], "correct_option": "Newton", "explanation": "Newton is the SI unit of Force.", "difficulty": "Easy"},
        {"subject": "Science", "topic": "Chemistry", "text": "pH of pure water?", "options": ["0", "7", "14", "1"], "correct_option": "7", "explanation": "Neutral pH is 7.", "difficulty": "Easy"},
        {"subject": "Science", "topic": "Biology", "text": "Universal Donor Blood Group?", "options": ["A", "B", "AB", "O-"], "correct_option": "O-", "explanation": "O negative is universal donor.", "difficulty": "Medium"},
    ]

    # Duplicate some to create volume for mock (simulating large DB)
    for i in range(5):
        for q in questions_data:
            # Shallow copy to modify text slightly to make them unique rows in DB
            new_q = models.Question(
                subject=q["subject"],
                topic=q["topic"],
                text=q["text"], # In real app we would have unique Qs
                options=q["options"],
                correct_option=q["correct_option"],
                explanation=q["explanation"],
                difficulty=q["difficulty"]
            )
            db.add(new_q)
    
    db.commit()
