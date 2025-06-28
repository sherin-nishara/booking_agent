from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .langgraph_agent import Agent
from .cal_utils import check_availability, create_event, list_events, cancel_event_by_time
from datetime import datetime

app = FastAPI()
agent = Agent()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and response models
class ChatRequest(BaseModel):
    message: str
    context: dict = {}

class ChatResponse(BaseModel):
    reply: str
    intent: str
    data: dict

@app.get("/")
async def root():
    return {"status": "✅ Booking agent backend is live!"}

@app.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Greeting shortcut
    greetings = ["hi", "hello", "heyy", "hey", "hai"]
    if req.message.lower().strip() in greetings:
        return ChatResponse(
            reply="👋 Hello! I'm your AI meeting assistant. You can ask me to *book*, *check*, *cancel* or *reschedule* meetings!",
            intent="greet",
            data={}
        )

    # NLP agent processing
    intent, data = agent.parse_intent(req.message, req.context)
    slots = agent.extract_time_slots(data) or {}

    start = slots.get("start")
    end = slots.get("end")
    reply = "❌ Couldn't understand your request."

    if start and end:
        is_free = check_availability(start, end)
    else:
        is_free = False

    # Intent handling
    if intent == "book_meeting":
        if start and end:
            if is_free:
                create_event(start, end)
                reply = f"📅 Meeting booked on {start.strftime('%A, %B %d, %Y')} from {start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}."
            else:
                reply = agent.reply_unavailable(slots)
        else:
            reply = "❌ Please specify a valid time to book the meeting."

    elif intent == "check_availability":
        reply = agent.reply_availability(is_free, slots)

    elif intent == "check_schedule":
        reply = list_events()

    elif intent == "cancel_meeting":
        if start and end:
            cancelled = cancel_event_by_time(start, end)
            reply = "✅ Meeting cancelled." if cancelled else "❌ No meeting found at that time to cancel."
        else:
            reply = "❌ Please specify the time of the meeting to cancel."

    elif intent == "reschedule_meeting":
        reply = "🔁 Rescheduling not implemented yet."

    return ChatResponse(reply=reply, intent=intent, data=data)
