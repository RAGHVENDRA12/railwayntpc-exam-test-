from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Gamification & Stats
    current_streak = Column(Integer, default=0)
    last_study_date = Column(DateTime, nullable=True)
    total_study_minutes = Column(Integer, default=0)
    points = Column(Integer, default=0) # For leaderboard

    results = relationship("QuizResult", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    study_logs = relationship("StudyLog", back_populates="user")
    mistakes = relationship("Mistake", back_populates="user")
    answers = relationship("UserAnswer", back_populates="user")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, index=True) # Maths, Reasoning, GK, Science
    topic = Column(String, index=True)   # Algebra, Blood Relations, Physics...
    text = Column(Text)
    options = Column(JSON) # List of strings ["A", "B", "C", "D"]
    correct_option = Column(String) # The actual answer text or index
    explanation = Column(Text)
    difficulty = Column(String, default="Medium") # Easy, Medium, Hard

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quiz_type = Column(String) # 'Topic Quiz', 'Mock Test', 'Revision'
    subject = Column(String, nullable=True) # If topic quiz
    score = Column(Float)
    total_questions = Column(Integer)
    attempted = Column(Integer)
    correct = Column(Integer)
    wrong = Column(Integer)
    accuracy = Column(Float)
    time_taken_seconds = Column(Integer)
    date = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="results")
    answers = relationship("UserAnswer", back_populates="result")

class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quiz_result_id = Column(Integer, ForeignKey("quiz_results.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_option = Column(String)
    is_correct = Column(Boolean)
    time_taken = Column(Integer) # Seconds for this specific question

    user = relationship("User", back_populates="answers")
    result = relationship("QuizResult", back_populates="answers")
    question = relationship("Question")

class Mistake(Base):
    __tablename__ = "mistakes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    count = Column(Integer, default=1) # How many times got wrong
    mastered = Column(Boolean, default=False) # If correctly answered later multiple times? 
    last_reviewed = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="mistakes")
    question = relationship("Question")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    completed = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.datetime.utcnow) # For daily planner
    type = Column(String, default="Custon") # 'System' (Auto-generated) or 'Custom'

    user = relationship("User", back_populates="tasks")

class StudyLog(Base):
    __tablename__ = "study_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    minutes = Column(Integer)
    activity = Column(String) # 'Quiz', 'Mock', 'Revision', 'Reading'

    user = relationship("User", back_populates="study_logs")
