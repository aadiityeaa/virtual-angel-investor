import streamlit as st
import requests
import time

# Backend API endpoints
BACKEND_URL = "http://127.0.0.1:5000"
UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/upload"
CONTINUE_ENDPOINT = f"{BACKEND_URL}/api/continue"
FINISH_ENDPOINT = f"{BACKEND_URL}/api/finish"

# --- Page Configuration ---
st.set_page_config(
    page_title="Virtual Angel Investor",
    page_icon="😇",
    layout="wide"
)

# --- Session State Initialization ---
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'interview_finished' not in st.session_state:
    st.session_state.interview_finished = False
if 'final_review' not in st.session_state:
    st.session_state.final_review = ""

# --- UI Components ---
st.title("😇 Virtual Angel Investor")
st.markdown("Upload your pitch deck to start the interview process.")

# --- Main Logic ---

# Step 1: File Upload
if not st.session_state.interview_started:
    uploaded_file = st.file_uploader(
        "Choose a pitch deck (PPTX, PDF, DOCX)",
        type=["pptx", "pdf", "docx"]
    )

    if uploaded_file is not None:
        with st.spinner("Analyzing your pitch deck and preparing the first question..."):
            try:
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(UPLOAD_ENDPOINT, files=files)

                if response.status_code == 200:
                    data = response.json()
                    first_question = data.get('question')
                    st.session_state.chat_history.append({"role": "assistant", "content": first_question})
                    st.session_state.interview_started = True
                    st.rerun() # Rerun to move to the chat interface
                else:
                    st.error(f"Error from server: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend. Make sure it's running. Error: {e}")


# Step 2: Chat Interface
if st.session_state.interview_started and not st.session_state.interview_finished:
    st.header("Investor Q&A")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    prompt = st.chat_input("Your answer...")
    if prompt:
        # Add user message to history and display it
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI's next question
        with st.spinner("Thinking..."):
            try:
                response = requests.post(CONTINUE_ENDPOINT, json={"answer": prompt})
                if response.status_code == 200:
                    data = response.json()
                    next_question = data.get('question')
                    st.session_state.chat_history.append({"role": "assistant", "content": next_question})
                    st.rerun() # Rerun to display the new question
                else:
                    st.error(f"Error from server: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend. Error: {e}")


    # Finish Interview Button
    if st.button("Finish Interview"):
        with st.spinner("Generating your final review..."):
            try:
                response = requests.post(FINISH_ENDPOINT)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.final_review = data.get('review')
                    st.session_state.interview_finished = True
                    st.rerun()
                else:
                    st.error(f"Error from server: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend. Error: {e}")

# Step 3: Final Review Display
if st.session_state.interview_finished:
    st.header("Final Investment Review")
    st.markdown(st.session_state.final_review)
    if st.button("Start New Interview"):
        # Reset all session state variables to start over
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()