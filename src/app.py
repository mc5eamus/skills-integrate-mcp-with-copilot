"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
import json
import hashlib
import secrets
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Load teacher credentials
teachers_file = current_dir / "teachers.json"
with open(teachers_file) as f:
    teachers = json.load(f)

# In-memory sessions
sessions = {}


class LoginRequest(BaseModel):
    username: str
    password: str


def verify_password(password: str, stored_hash: str) -> bool:
    salt, hash_val = stored_hash.split(":")
    computed = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100000
    ).hex()
    return secrets.compare_digest(computed, hash_val)


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/auth/login")
def login(request: LoginRequest):
    """Authenticate a teacher"""
    if request.username not in teachers:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(request.password, teachers[request.username]["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_hex(32)
    sessions[token] = request.username
    return {"token": token, "username": teachers[request.username]["display_name"]}


@app.post("/auth/logout")
def logout(authorization: str = Header(None)):
    """Log out a teacher"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        sessions.pop(token, None)
    return {"message": "Logged out"}


@app.get("/auth/status")
def auth_status(authorization: str = Header(None)):
    """Check authentication status"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        username = sessions.get(token)
        if username:
            return {
                "authenticated": True,
                "username": teachers[username]["display_name"],
            }
    return {"authenticated": False}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, authorization: str = Header(None)):
    """Sign up a student for an activity (teacher login required)"""
    # Verify teacher is logged in
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Teacher login required")
    token = authorization[7:]
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Teacher login required")

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, authorization: str = Header(None)):
    """Unregister a student from an activity (teacher login required)"""
    # Verify teacher is logged in
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Teacher login required")
    token = authorization[7:]
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Teacher login required")

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
