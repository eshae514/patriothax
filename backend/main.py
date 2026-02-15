# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import serial, threading, time, re, os
from fastapi.responses import StreamingResponse
import asyncio
import json

# --------------------
# GEMINI SETUP
# --------------------
client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

# --------------------
# FASTAPI SETUP
# --------------------
app = FastAPI(title="Heartbeat AI Coach")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# HEART RATE STATE
# --------------------
latest_bpm = None
bpm_history = []
measuring = False
start_time = 0
MEASURE_DURATION = 10000  # 10 seconds after finger detected

# --------------------
# SERIAL THREAD
# --------------------
def read_arduino():
    global latest_bpm, bpm_history, measuring, start_time
    try:
        ser = serial.Serial("COM8", 115200, timeout=1)
        time.sleep(2)
        print("Connected to Arduino")

        while True:
            line = ser.readline().decode(errors="ignore").strip()
            match = re.search(r"BPM:\s*(\d+\.?\d*)", line)
            if match:
                bpm = float(match.group(1))
                latest_bpm = bpm

                if measuring:
                    bpm_history.append({"time": time.time() - start_time, "bpm": bpm})

    except Exception as e:
        print("Serial error:", e)

threading.Thread(target=read_arduino, daemon=True).start()

# --------------------
# STREAMING BPM
# --------------------
@app.get("/bpm_stream")
async def bpm_stream():
    global measuring, start_time, bpm_history

    # Reset for a new measurement
    bpm_history = []
    measuring = True
    start_time = time.time()

    async def event_generator():
        global measuring
        while measuring:
            if latest_bpm:
                yield f"data:{json.dumps({'bpm': latest_bpm})}\n\n"
            await asyncio.sleep(0.1)  # 10 updates per second

            # Stop after MEASURE_DURATION
            if time.time() - start_time >= MEASURE_DURATION / 1000:
                measuring = False

        # After measurement, send AI advice
        avg_bpm = sum([d['bpm'] for d in bpm_history])/len(bpm_history) if bpm_history else 0
        stress = "stressed" if avg_bpm > 90 else "relaxed"

        prompt = f"""
You are a student support AI.
Heart rate average over 10 seconds: {avg_bpm} BPM.
The student seems {stress}.

Give ONE insight and THREE short study actions.
Format:
Title:
Insight:
- Step 1
- Step 2
- Step 3
"""

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = response.text
        except Exception as e:
            print("Gemini error:", e)
            text = """Title: Heartbeat Detected
Insight: AI unavailable, but measurement finished.
- Take a slow breath
- Relax your shoulders
- Try again later
"""

        # Parse AI output
        out = {"title": "", "insight": "", "steps": []}
        current = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("Title:"):
                out["title"] = line[6:].strip()
            elif line.startswith("Insight:"):
                out["insight"] = line[8:].strip()
            elif line.startswith("-"):
                out["steps"].append(line[1:].strip())

        yield f"data:{json.dumps({'ai': out})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
