import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

FASTAPI_URI = os.getenv("FASTAPI_URI")

def set_global_config():
    st.set_page_config(
        page_title="CV Vector",
        layout="centered",
        initial_sidebar_state="collapsed"
    )