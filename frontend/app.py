import streamlit as st
import requests
import os

BACKEND_URL = "https://booking-backend-aqim.onrender.com"

st.set_page_config(page_title="Booking Agent", layout="centered")
st.title("🤖 AI Booking Assistant")

# Session setup
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I'm your AI meeting assistant. You can ask me to **book**, **cancel**, **reschedule**, or **view** your meetings.\n\nTry asking:\n- 'Book a meeting tomorrow at 3PM'\n- 'Cancel my 5PM meeting on Friday'\n- 'What's my schedule for next Tuesday?'"}
    ]
if "context" not in st.session_state:
    st.session_state.context = {}

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat input
user_input = st.chat_input("Ask me something like: 'Book meeting tomorrow at 3PM'")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        try:
            response = requests.post("https://booking-backend-aqim.onrender.com/", json={
                "message": user_input,
                "context": st.session_state.context
            })
            response.raise_for_status()
            res = response.json()
            reply = res.get("reply", "No response from backend.")
            st.session_state.context = res.get("data", {})
        except requests.exceptions.RequestException as e:
            reply = f"❌ Backend connection error:\n\n`{e}`"
        except ValueError:
            reply = "❌ Invalid JSON response from backend."
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# Divider + View Schedule
st.divider()
if st.button("📅 View My Schedule (next 2 days)"):
    with st.spinner("Fetching schedule..."):
        try:
            response = requests.post("https://booking-backend-aqim.onrender.com/", json={
                "message": "What’s my schedule?",
                "context": {}
            })
            reply = response.json().get("reply", "⚠️ Failed to fetch schedule.")
        except:
            reply = "❌ Could not connect to backend."
    st.chat_message("assistant").write(reply)
