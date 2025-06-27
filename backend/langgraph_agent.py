import os
import json
import dateparser
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.chat_models import ChatOpenAI
from datetime import datetime, timedelta

load_dotenv()

llm = ChatOpenAI(
    openai_api_key=os.getenv("GROQ_API_KEY"),
    openai_api_base="https://api.groq.com/openai/v1",
    model="llama-3.3-70b-versatile",
    temperature=0.7
)

class Agent:
    def parse_intent(self, text, ctx={}):
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
                Extract the user's intent and time in JSON. 
                Possible intents: ["book_meeting", "cancel_meeting", "reschedule_meeting", "check_availability", "check_schedule"]
                Include ISO 8601 format time where possible.
                Reply like: 
                {
                    "intent": "book_meeting",
                    "start": "2025-06-29T15:00",
                    "end": "2025-06-29T16:00"
                }
                If not enough info, set start or end to null.
            """),
            HumanMessage(content=text)
        ])
        result = (prompt | llm).invoke({})
        print("📥 Raw LLM output:", result.content)
        try:
            parsed = json.loads(result.content.replace("'", '"'))
            return parsed["intent"], parsed
        except Exception as e:
            print("❌ Parse Error:", e)
            return "unknown", {}

    def extract_time_slots(self, entities):
        def clean(text):
            if not isinstance(text, str):
                return text
            text = text.lower().strip()
            if "next tomorrow" in text:
                return "day after tomorrow"
            return text

        start_str = clean(entities.get("start"))
        end_str = clean(entities.get("end"))

        parsed_start = dateparser.parse(start_str) if isinstance(start_str, str) else None
        parsed_end = dateparser.parse(end_str) if isinstance(end_str, str) else None

        if parsed_start and not parsed_end:
            parsed_end = parsed_start + timedelta(hours=1)

        return {
            "start": parsed_start,
            "end": parsed_end,
        }

    def reply_availability(self, free, slots):
        if slots["start"] and slots["end"]:
            return (
                f"{'✅ You are free' if free else '❌ You are not available'} on "
                f"{slots['start'].strftime('%A, %B %d, %Y')} from "
                f"{slots['start'].strftime('%I:%M %p')} to "
                f"{slots['end'].strftime('%I:%M %p')}."
            )
        else:
            return "❌ Couldn't understand the time. Please try again."

    def reply_unavailable(self, slots):
        return "That slot is not available. Please choose another time."
