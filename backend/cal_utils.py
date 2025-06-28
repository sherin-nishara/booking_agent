from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import dateparser
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = f"/etc/secrets/{os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')}"

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)
CALENDAR_ID = 'sherinars2004@gmail.com'

def check_availability(start_dt: datetime, end_dt: datetime) -> bool:
    events = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_dt.isoformat() + 'Z',
        timeMax=end_dt.isoformat() + 'Z',
        singleEvents=True
    ).execute().get('items', [])
    return len(events) == 0

def create_event(start_dt: datetime, end_dt: datetime, summary="Meeting"):
    event = {
        "summary": summary,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"}
    }
    return service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

def list_events():
    now = datetime.utcnow().isoformat() + 'Z'
    later = (datetime.utcnow() + timedelta(days=3)).isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=CALENDAR_ID, timeMin=now, timeMax=later,
        maxResults=10, singleEvents=True, orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        return "📭 No upcoming events found."
    
    msg = "📅 Here are your upcoming meetings:\n"
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start_dt = datetime.fromisoformat(start)
        msg += f"- {event['summary']} on {start_dt.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
    return msg

from datetime import datetime
import pytz

def cancel_event_by_time(start_dt: datetime, end_dt: datetime) -> str:
    tz = pytz.timezone("Asia/Kolkata")
    start_dt = tz.localize(start_dt) if start_dt.tzinfo is None else start_dt
    end_dt = tz.localize(end_dt) if end_dt.tzinfo is None else end_dt

    events = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True
    ).execute().get('items', [])

    for event in events:
        event_start_str = event['start'].get('dateTime')
        if not event_start_str:
            continue

        event_start = datetime.fromisoformat(event_start_str.replace("Z", "+00:00"))
        if abs((event_start - start_dt).total_seconds()) < 60:
            service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
            return f"🗑️ Event '{event['summary']}' at {event_start.strftime('%I:%M %p')} cancelled."

    return "❌ No meeting found at that time to cancel."


