from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langgraph_agent import Agent
from cal_utils import check_availability, create_event, list_events, cancel_event_by_time
from datetime import datetime

app = FastAPI()
agent = Agent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    context: dict = {}

class ChatResponse(BaseModel):
    reply: str
    intent: str
    data: dict
    
@app.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Greeting check
    greetings = ["hi", "hello", "heyy", "hey", "hai"]
    if req.message.lower().strip() in greetings:
        return ChatResponse(reply="👋 Hello! I'm your AI meeting assistant. You can ask me to *book*, *check*, *cancel* or *reschedule* meetings!", intent="greet", data={})

    intent, data = agent.parse_intent(req.message, req.context)
    slots = agent.extract_time_slots(data)
    reply = "❌ Couldn't understand your request."

    if slots["start"] and slots["end"]:
        is_free = check_availability(slots["start"], slots["end"])
    else:
        is_free = False

    if intent == "book_meeting":
        if slots["start"] and slots["end"]:
            if is_free:
                create_event(slots["start"], slots["end"])
                reply = f"📅 Meeting booked on {slots['start'].strftime('%A, %B %d, %Y')} from {slots['start'].strftime('%I:%M %p')} to {slots['end'].strftime('%I:%M %p')}."
            else:
                reply = agent.reply_unavailable(slots)
        else:
            reply = "❌ Please specify a valid time to book the meeting."

    elif intent == "check_availability":
        reply = agent.reply_availability(is_free, slots)

    elif intent == "check_schedule":
        reply = list_events()

    elif intent == "cancel_meeting":
        cancelled = cancel_event_by_time(slots["start"], slots["end"])
        reply = "✅ Meeting cancelled." if cancelled else "❌ No meeting found at that time to cancel."


    elif intent == "reschedule_meeting":
        reply = "🔁 Rescheduling not implemented yet."

    return ChatResponse(reply=reply, intent=intent, data=data)
