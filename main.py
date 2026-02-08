from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from passlib.context import CryptContext
from datetime import datetime, timedelta
import random
import json

import models
import database

# Initialize DB
database.init_db()

templates = Jinja2Templates(directory="templates")
# Custom filters
def round_filter(value, precision=2):
    return round(value, precision)
templates.env.filters["round"] = round_filter
templates.env.filters["tojson"] = json.dumps

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth Helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id: return None
    return db.query(models.User).filter(models.User.id == user_id).first()

# Session Middleware
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == username).first():
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username taken"})
    
    new_user = models.User(username=username, hashed_password=get_password_hash(password))
    db.add(new_user)
    db.commit()
    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid details"})
    
    # Update login Streak logic
    today = datetime.utcnow().date()
    if user.last_study_date:
        delta = (today - user.last_study_date.date()).days
        if delta == 1:
            user.current_streak += 1
        elif delta > 1:
            user.current_streak = 1 # Reset if missed a day
    else:
        user.current_streak = 1
        
    user.last_study_date = datetime.utcnow()
    db.commit()
    
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    
    # Logic: "What to study today"
    # Find weak subject (lowest accuracy)
    results = db.query(models.QuizResult).filter(models.QuizResult.user_id == user.id).all()
    subject_stats = {} # {subj: [correct, total]}
    for r in results:
        if r.subject:
            if r.subject not in subject_stats: subject_stats[r.subject] = [0, 0]
            subject_stats[r.subject][0] += r.correct
            subject_stats[r.subject][1] += r.total_questions
            
    weak_subject = "Maths" # Default
    min_acc = 100
    for subj, stats in subject_stats.items():
        acc = (stats[0] / stats[1]) * 100 if stats[1] > 0 else 0
        if acc < min_acc and stats[1] > 10: # Only if significant data
            min_acc = acc
            weak_subject = subj
            
    # Mock auto-tasks for planner
    tasks = db.query(models.Task).filter(models.Task.user_id == user.id, models.Task.completed == False).all()
    if not tasks:
        # Auto generate daily plan
        t1 = models.Task(user_id=user.id, title=f"Practice 20 Qs of {weak_subject}", type="System")
        t2 = models.Task(user_id=user.id, title="Take 1 Mock Test", type="System")
        db.add(t1)
        db.add(t2)
        db.commit()
        tasks = [t1, t2]

    total_tasks = db.query(models.Task).filter(models.Task.user_id == user.id).count()
    completed_tasks = db.query(models.Task).filter(models.Task.user_id == user.id, models.Task.completed == True).count()
    progress = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user, 
        "tasks": tasks, "weak_subject": weak_subject,
        "progress": progress
    })

# --- Quiz System ---

@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request, topic: str = "Maths", count: int = 10, db: Session = Depends(get_db)):
    if not request.session.get("user_id"): return RedirectResponse("/login")
    
    # Fetch questions from DB
    qs = db.query(models.Question).filter(models.Question.subject == topic).all()
    if not qs:
        # Fallback to random ANY if specific topic empty (for demo safety)
        qs = db.query(models.Question).all()
    
    if len(qs) < count:
         # repeat if not enough
         qs = qs * (count // len(qs) + 1)
         
    selected_qs = random.sample(qs, min(count, len(qs)))
    
    # Serialize for frontend
    questions_json = []
    for q in selected_qs:
        questions_json.append({
            "id": q.id,
            "text": q.text,
            "options": q.options,
            "subject": q.subject
        })
        
    return templates.TemplateResponse("quiz.html", {
        "request": request, 
        "topic": topic, 
        "questions": questions_json,
        "total": len(questions_json)
    })

@app.post("/submit_quiz_api")
async def submit_quiz_api(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return JSONResponse(status_code=401, content={"msg": "Login required"})
    
    data = await request.json()
    # data format: { topic: str, answers: { q_id: option_text }, time_taken: int, type: str }
    
    correct_count = 0
    attempted_count = 0
    total_q = len(data['answers'])
    
    # Create Result Entry first
    result = models.QuizResult(
        user_id=user.id,
        quiz_type=data.get('type', 'Quiz'),
        subject=data.get('topic'),
        total_questions=total_q,
        time_taken_seconds=data.get('time_taken', 0),
        attempted=0, correct=0, wrong=0, score=0, accuracy=0
    )
    db.add(result)
    db.flush() # Get ID
    
    for q_id, selected_opt in data['answers'].items():
        q_id = int(q_id)
        q = db.query(models.Question).filter(models.Question.id == q_id).first()
        if not q: continue
        
        is_right = False
        if selected_opt:
            attempted_count += 1
            if selected_opt == q.correct_option:
                correct_count += 1
                is_right = True
            else:
                # Log mistake
                mistake = db.query(models.Mistake).filter(models.Mistake.user_id==user.id, models.Mistake.question_id==q.id).first()
                if mistake:
                    mistake.count += 1
                    mistake.mastered = False
                    mistake.last_reviewed = datetime.utcnow()
                else:
                    mistake = models.Mistake(user_id=user.id, question_id=q.id)
                    db.add(mistake)
        
        # Save detailed answer
        ans = models.UserAnswer(
            user_id=user.id,
            quiz_result_id=result.id,
            question_id=q.id,
            selected_option=selected_opt,
            is_correct=is_right
        )
        db.add(ans)
        
    wrong_count = attempted_count - correct_count
    score = correct_count - (wrong_count * 0.33) # Negative marking
    
    result.attempted = attempted_count
    result.correct = correct_count
    result.wrong = wrong_count
    result.score = round(score, 2)
    result.accuracy = round((correct_count / attempted_count * 100) if attempted_count > 0 else 0, 2)
    
    # Update user stats
    user.points += int(score * 10)
    user.total_study_minutes += (data.get('time_taken', 0) // 60)
    
    # Log study time
    log = models.StudyLog(user_id=user.id, minutes=(data.get('time_taken', 0)//60), activity=data.get('type', 'Quiz'))
    db.add(log)
    
    db.commit()
    
    return {"status": "success", "result_id": result.id}

@app.get("/result/{result_id}", response_class=HTMLResponse)
async def result_page(request: Request, result_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse("/login")
    
    result = db.query(models.QuizResult).filter(models.QuizResult.id == result_id).first()
    # Fetch detailed answers for review
    answers = db.query(models.UserAnswer).filter(models.UserAnswer.quiz_result_id == result_id).all()
    
    return templates.TemplateResponse("result.html", {
        "request": request, 
        "result": result,
        "answers": answers
    })

@app.get("/mock", response_class=HTMLResponse)
async def mock_page(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"): return RedirectResponse("/login")
    
    # Generate 100 Qs similar to seed logic but random selection
    all_qs = db.query(models.Question).all()
    # Should ideally pick by subject mix (30 Math, 30 Reas, 40 GK)
    # Simplified:
    if len(all_qs) < 100:
        qs = all_qs * (100 // len(all_qs) + 1)
        qs = qs[:100]
    else:
        qs = random.sample(all_qs, 100)
        
    questions_json = []
    for q in qs:
        questions_json.append({
            "id": q.id, "text": q.text, "options": q.options, "subject": q.subject
        })
        
    return templates.TemplateResponse("mock.html", {
        "request": request, "questions": questions_json
    })

# --- Features ---

@app.get("/planner", response_class=HTMLResponse)
async def planner_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse("/login")
    tasks = db.query(models.Task).filter(models.Task.user_id == user.id).all()
    return templates.TemplateResponse("planner.html", {"request": request, "tasks": tasks})

@app.post("/manage_task")
async def manage_task(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    data = await request.json()
    action = data.get('action') 
    
    if action == 'add':
        t = models.Task(user_id=user.id, title=data.get('title'))
        db.add(t)
    elif action == 'toggle':
        t = db.query(models.Task).get(data.get('id'))
        if t and t.user_id == user.id: t.completed = not t.completed
    elif action == 'delete':
        t = db.query(models.Task).get(data.get('id'))
        if t and t.user_id == user.id: db.delete(t)
        
    db.commit()
    return {"status": "ok"}

@app.post("/mark_mastered")
async def mark_mastered(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return JSONResponse(status_code=401, content={"msg": "Login required"})
    
    data = await request.json()
    q_id = data.get('question_id')
    
    mistake = db.query(models.Mistake).filter(models.Mistake.user_id == user.id, models.Mistake.question_id == q_id).first()
    if mistake:
        mistake.mastered = True
        db.commit()
        return {"status": "success"}
    return {"status": "error", "msg": "Mistake not found"}

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse("/login")
    
    results = db.query(models.QuizResult).filter(models.QuizResult.user_id == user.id).order_by(models.QuizResult.date.desc()).all()
    
    # Pre-process data for charts to avoid template complexity
    chart_data = []
    for r in results:
        chart_data.append({
            "subject": r.subject or "Mix",
            "score": r.score,
            "date": r.date.strftime("%Y-%m-%d"),
            "total": r.total_questions
        })
    
    return templates.TemplateResponse("analytics.html", {
        "request": request, 
        "results": results, 
        "chart_data": chart_data,
        "avg_score": round(sum([r.score for r in results])/len(results), 1) if results else 0,
        "total_tests": len(results)
    })

@app.get("/revision", response_class=HTMLResponse)
async def revision_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse("/login")
    
    # Get mistakes not mastered
    mistakes = db.query(models.Mistake).filter(models.Mistake.user_id == user.id, models.Mistake.mastered == False).all()
    
    questions = []
    for m in mistakes:
        questions.append(m.question)
        
    return templates.TemplateResponse("revision.html", {"request": request, "questions": questions})

@app.get("/focus", response_class=HTMLResponse)
async def focus_page(request: Request):
    if not request.session.get("user_id"): return RedirectResponse("/login")
    return templates.TemplateResponse("focus.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    # Use import string "main:app" with reload=True for auto-reload
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
