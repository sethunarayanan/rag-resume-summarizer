import os
import io
import json
import threading
import requests
import streamlit as st
import websocket
import logging
from queue import Queue
from config.settings import set_global_config

set_global_config()
logging.basicConfig(level=logging.INFO)

FASTAPI_URI = os.getenv("FASTAPI_URI")
WS_URI = os.getenv("WS_URI")

st.title("Resume Summarizer (RAG Prototype)")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")

status_placeholder = st.empty()
summary_placeholder = st.empty()

ws_queue = Queue()

if "uploading" not in st.session_state:
    st.session_state.uploading = False
if "summary_ready" not in st.session_state:
    st.session_state.summary_ready = False

def on_message(ws, message):
    logging.info(f"WebSocket message received: {message}")
    ws_queue.put(message)

def on_error(ws, error):
    logging.error(f"WebSocket error: {error}")
    ws_queue.put(json.dumps({"status": "error", "error": str(error)}))

def on_close(ws, close_status_code, close_msg):
    logging.info(f"WebSocket closed: {close_status_code}, {close_msg}")
    ws_queue.put(json.dumps({"status": "closed"}))

def start_ws(resume_id: str):
    ws_url = f"{WS_URI}ws/resume/{resume_id}"
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    logging.info("Starting WebSocket connection...")
    ws.run_forever()

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    uploaded_file_name = uploaded_file.name
    btn_label = "Processing..." if st.session_state.uploading else "Submit Resume"
    btn_disabled = st.session_state.uploading or st.session_state.summary_ready
    if st.button(btn_label, disabled=btn_disabled):
        st.session_state.uploading = True
        status_placeholder.text("Uploading your resume...")
        files = {
            "file": (uploaded_file_name, io.BytesIO(file_bytes), "application/pdf")
        }
        try:
            response = requests.post(f"{FASTAPI_URI}resume_upload", files=files)
            response.raise_for_status()
            data = response.json().get("data", {})
            resume_id = data.get("resume_id")
            if resume_id:
                status_placeholder.text("Resume uploaded")
                threading.Thread(target=start_ws, args=(resume_id,), daemon=True).start()
                while True:
                    try:
                        msg = ws_queue.get(timeout=0.5)
                        data = json.loads(msg)
                        status = data.get("status")
                        if status == "processing":
                            status_placeholder.text("Processing your resume...")
                        elif status in ("done", "complete"):
                            status_placeholder.text("Summary ready")
                            summary_placeholder.markdown(
                                f"### Resume Summary\n\n>{data.get('summary','')}"
                            )
                            st.session_state.uploading = False
                            st.session_state.summary_ready = True
                            status_placeholder.empty()
                            break
                        elif status == "error":
                            status_placeholder.text(f"WebSocket error: {data.get('error')}")
                            st.session_state.uploading = False
                            break
                        elif status == "closed":
                            break
                    except Exception:
                        st.rerun()
            else:
                st.error("No resume_id returned from backend")
                st.session_state.uploading = False
        except Exception as e:
            logging.error(f"Upload failed: {e}")
            st.error(f"Upload failed: {e}")
            st.session_state.uploading = False