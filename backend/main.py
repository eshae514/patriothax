from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

# --------------------
# SETUP
# --------------------

client = genai.Client(api_key="AIzaSyA3l1vHt-mDOHNoAq7vEnLNDTcwHiuD36I")

app = FastAPI(title="Heartbeat AI Coach")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# REQUEST MODEL
# --------------------

class HeartbeatRequest(BaseModel):
    bpm: int

# --------------------
# PARSER
# --------------------

def parse_ai_response(text: str):
    sections = {
        "title": "",
        "insight": "",
        "steps": []
    }

    current = None

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("Title:"):
            sections["title"] = line.replace("Title:", "").strip()

        elif line.startswith("Insight:"):
            current = "insight"
            sections["insight"] = line.replace("Insight:", "").strip()

        elif line.startswith("Action Steps:"):
            current = "steps"

        elif line.startswith("-") and current == "steps":
            sections["steps"].append(line[1:].strip())

    return sections

# --------------------
# ENDPOINT
# --------------------

@app.post("/generate")
async def generate_advice(request: HeartbeatRequest):
    bpm = request.bpm

    prompt = f"""
You are an educational support assistant for students.

Context:
- Hackathon education project
- Student heart rate: {bpm} BPM
- Goal: help with focus, studying, or test readiness
- No medical advice

Output format:
Title:
Insight:
Action Steps:
- Step 1
- Step 2
- Step 3

Rules:
- Max 6 sentences total
- Supportive, calm, student-friendly
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    parsed = parse_ai_response(response.text)

    return {
        "bpm": bpm,
        "title": parsed["title"],
        "insight": parsed["insight"],
        "steps": parsed["steps"]
    }

# --------------------
# HEALTH CHECK
# --------------------

@app.get("/")
def root():
    return {"status": "Heartbeat AI Coach running"}
