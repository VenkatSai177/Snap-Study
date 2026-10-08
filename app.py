import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import prompts
from PIL import Image
import io
import logging
import re
import html
import time

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="StudySnap AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# LOGGING SETUP
# ==========================================
logger = logging.getLogger("studysnap")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ==========================================
# CONSTANTS
# ==========================================
MODEL_NAME = "gemini-3.6-flash"

# ==========================================
# HELPERS
# ==========================================
def get_secret(key, default=None):
    try:
        from streamlit.errors import StreamlitAPIException
    except ImportError:
        StreamlitAPIException = Exception
        
    try:
        return st.secrets.get(key, default)
    except FileNotFoundError:
        return default
    except Exception as e:
        if type(e).__name__ in ["StreamlitSecretNotFoundError", "StreamlitAPIException"]:
            return default
        logger.error(f"Configuration error: {type(e).__name__}")
        return default

def show_error(message, title="⚠️ Something went wrong"):
    st.markdown(f"""
        <div class="premium-error animate-entrance">
            <div class="premium-error-title">{title}</div>
            <div class="premium-error-body">{message}</div>
        </div>
    """, unsafe_allow_html=True)


# ==========================================
# CUSTOM CSS & THEMING
# ==========================================
# ==========================================
# CUSTOM CSS & THEMING
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* -----------------------------------------
       LIQUID BACKGROUND MOTION & BASE
    ------------------------------------------ */
    .stApp {
        background-color: #F8FAFC;
        color: #1F2937 !important;
        overflow-x: hidden;
    }
    
    .stApp::before, .stApp::after {
        content: "";
        position: fixed;
        width: 600px;
        height: 600px;
        border-radius: 50%;
        filter: blur(70px);
        z-index: -1;
        pointer-events: none;
    }
    
    .stApp::before {
        background: radial-gradient(circle, rgba(99,102,241,0.12), transparent 60%);
        top: -100px;
        left: -100px;
        animation: floatBlob 18s ease-in-out infinite alternate;
    }
    
    .stApp::after {
        background: radial-gradient(circle, rgba(14,165,233,0.1), transparent 60%);
        bottom: -100px;
        right: -100px;
        animation: floatBlob2 20s ease-in-out infinite alternate-reverse;
    }
    
    @keyframes floatBlob {
        0% { transform: translate3d(0, 0, 0) scale(1); }
        100% { transform: translate3d(80px, 40px, 0) scale(1.05); }
    }
    
    @keyframes floatBlob2 {
        0% { transform: translate3d(0, 0, 0) scale(1); }
        100% { transform: translate3d(-60px, -50px, 0) scale(1.1); }
    }
    
    @media (prefers-reduced-motion: reduce) {
        .stApp::before, .stApp::after {
            animation: none !important;
        }
    }

    /* -----------------------------------------
       GLASSMORPHISM CLASSES
    ------------------------------------------ */
    .glass-card {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(18px) saturate(140%);
        -webkit-backdrop-filter: blur(18px) saturate(140%);
        border: 1px solid rgba(255, 255, 255, 0.55);
        box-shadow: 0 8px 30px rgba(15, 23, 42, 0.06);
        border-radius: 18px;
    }
    
    .animate-entrance {
        animation: fadeUp 450ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    
    @keyframes fadeUp {
        0% { opacity: 0; transform: translateY(12px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    /* -----------------------------------------
       LAYOUT CONSTRAINTS
    ------------------------------------------ */
    [data-testid="block-container"] {
        max-width: 960px !important;
        padding-top: 2rem !important;
        padding-bottom: 6rem !important;
        margin: 0 auto;
    }

    /* -----------------------------------------
       SIDEBAR PREMIUM STYLING
    ------------------------------------------ */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.72) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(15, 23, 42, 0.06);
        min-width: 260px;
        max-width: 290px;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #4B5563 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
        color: #111827 !important;
        font-weight: 700;
    }
    
    /* -----------------------------------------
       TYPOGRAPHY & AI CHAT WORKSPACE
    ------------------------------------------ */
    :not(button) > [data-testid="stMarkdownContainer"] p, 
    :not(button) > [data-testid="stMarkdownContainer"] li,
    :not(button) > [data-testid="stMarkdownContainer"] ol,
    :not(button) > [data-testid="stMarkdownContainer"] ul,
    :not(button) > [data-testid="stText"] {
        color: #374151 !important;
        line-height: 1.6;
    }
    
    :not(button) > [data-testid="stMarkdownContainer"] h1,
    :not(button) > [data-testid="stMarkdownContainer"] h2,
    :not(button) > [data-testid="stMarkdownContainer"] h3,
    :not(button) > [data-testid="stMarkdownContainer"] h4,
    :not(button) > [data-testid="stMarkdownContainer"] h5,
    :not(button) > [data-testid="stMarkdownContainer"] h6,
    :not(button) > [data-testid="stMarkdownContainer"] strong,
    :not(button) > [data-testid="stMarkdownContainer"] b {
        color: #111827 !important;
        font-weight: 650;
    }
    
    :not(button) > [data-testid="stMarkdownContainer"] h3 {
        border-bottom: 1px solid rgba(15, 23, 42, 0.08);
        padding-bottom: 0.4rem;
        margin-bottom: 1rem;
        margin-top: 1.5rem;
    }
    
    /* -----------------------------------------
       CODE BLOCKS & INLINE CODE
    ------------------------------------------ */
    [data-testid="stMarkdownContainer"] p code,
    [data-testid="stMarkdownContainer"] li code {
        background-color: #F3F4F6 !important;
        color: #111827 !important;
        border-radius: 6px;
        padding: 0.2em 0.4em;
        border: 1px solid rgba(15,23,42,0.05);
    }
    
    [data-testid="stMarkdownContainer"] pre {
        background-color: #111827 !important;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 1rem;
    }
    
    [data-testid="stMarkdownContainer"] pre code {
        background-color: transparent !important;
        color: #F9FAFB !important;
    }

    /* -----------------------------------------
       USER VS AI CHAT BUBBLES
    ------------------------------------------ */
    /* Streamlit Default Chat Bubbles styling */
    [data-testid="stChatMessage"] {
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        background: transparent;
    }
    
    /* User Message Styling */
    [data-testid="chat-message-user"] {
        background: rgba(99, 102, 241, 0.05) !important;
        border: 1px solid rgba(99, 102, 241, 0.12) !important;
    }
    
    /* Model Message Styling */
    [data-testid="chat-message-model"] {
        background: transparent !important;
    }
    
    [data-testid="chat-message-user"] [data-testid="stMarkdownContainer"] p {
        color: #1F2937 !important;
    }

    /* -----------------------------------------
       CHAT INPUT (FLOATING COMMAND BAR)
    ------------------------------------------ */
    [data-testid="stChatInput"] {
        background-color: #1F212B !important;
        border-radius: 18px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        box-shadow: 0 12px 30px rgba(0,0,0,0.15) !important;
        padding: 4px 8px;
    }
    
    [data-testid="stChatInput"] textarea {
        color: #F9FAFB !important;
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #9CA3AF !important;
    }
    
    /* -----------------------------------------
       IMAGE ATTACHMENT
    ------------------------------------------ */
    div[data-testid="stImage"] {
        display: flex;
        justify-content: center;
        background: transparent;
        margin-top: 0.5rem;
    }
    
    div[data-testid="stImage"] img {
        max-height: 420px !important;
        object-fit: contain !important;
        width: auto !important;
        border-radius: 14px;
        box-shadow: 0 4px 20px rgba(15,23,42,0.08);
    }
    
    /* -----------------------------------------
       BUTTONS & QUICK ACTIONS
    ------------------------------------------ */
    button [data-testid="stMarkdownContainer"] p,
    button p {
        color: inherit !important;
    }
    
    /* Primary Action Buttons (like "Analyze Image Now") */
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
        border: none !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        transition: all 200ms ease !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.2) !important;
    }
    
    button[data-testid="baseButton-primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Secondary/Quick Action Buttons */
    button[data-testid="baseButton-secondary"] {
        background: rgba(99, 102, 241, 0.04) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        color: #374151 !important;
        border-radius: 12px !important;
        transition: all 180ms ease !important;
    }
    
    button[data-testid="baseButton-secondary"]:hover {
        background: rgba(99, 102, 241, 0.08) !important;
        color: #111827 !important;
    }
    
    /* -----------------------------------------
       ALERTS (Red Error & Green Success)
    ------------------------------------------ */
    .premium-error {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 1rem;
    }
    .premium-error-title {
        color: #991B1B;
        font-weight: 600;
        margin-bottom: 4px;
        font-size: 0.95rem;
    }
    .premium-error-body {
        color: #7F1D1D;
        font-size: 0.9rem;
    }
    
    /* -----------------------------------------
       MISC FIXES
    ------------------------------------------ */
    [data-testid="stWidgetLabel"] p {
        color: #1F2937 !important;
        font-weight: 500;
    }
    
    /* Suppress excessive Streamlit padding */
    .st-emotion-cache-183lzff {
        padding-top: 1rem !important;
    }
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "student_email" not in st.session_state:
    st.session_state.student_email = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0

# ==========================================
# GEMINI CLIENT & ERROR HANDLING
# ==========================================
def get_gemini_client():
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        return None
    return _create_gemini_client(api_key)

@st.cache_resource
def _create_gemini_client(api_key):
    return genai.Client(api_key=api_key)

def handle_gemini_error(e):
    code = getattr(e, 'code', 'Unknown')
    logger.error(f"Gemini API error | Type: {type(e).__name__} | Code: {code}")
    
    error_str = str(e).lower()
    
    if isinstance(e, APIError):
        if e.code == 401 or e.code == 403:
            return "Gemini authentication failed. Please verify your API key."
        elif e.code == 404:
            return "The selected Gemini model is currently unavailable."
        elif e.code == 429:
            return "Gemini API usage limit reached. Please try again later."
        elif e.code >= 500:
            return "Gemini services are currently experiencing issues. Please try again later."
    
    if "401" in error_str or "403" in error_str or "auth" in error_str:
        return "Gemini authentication failed. Please verify your API key."
    elif "404" in error_str or "not found" in error_str:
        return "The selected Gemini model is currently unavailable."
    elif "429" in error_str or "quota" in error_str or "rate limit" in error_str:
        return "Gemini API usage limit reached. Please try again later."
    elif "network" in error_str or "connection" in error_str:
        return "Unable to reach Gemini right now. Please check your connection."
    
    return "Gemini couldn't process that request right now. Check your API key, model access, quota, or connection."

def init_chat_session():
    client = get_gemini_client()
    if not client:
        return None
        
    config = types.GenerateContentConfig(
        system_instruction=prompts.SYSTEM_PROMPT,
        temperature=0.7
    )
    return client.chats.create(model=MODEL_NAME, config=config)

# ==========================================
# EMAIL FUNCTIONALITY
# ==========================================
def send_summary_email(summary_text):
    try:
        sender_email = get_secret("GMAIL_ADDRESS")
        sender_password = get_secret("GMAIL_APP_PASSWORD")
        receiver_email = st.session_state.student_email

        if not sender_email or not sender_password:
            return False, "Email summary is unavailable until Gmail is configured."

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = "StudySnap AI — Your Study Session Summary"

        msg.attach(MIMEText(summary_text, 'plain', 'utf-8'))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            
        return True, ""
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP error | Type: SMTPAuthenticationError")
        return False, "Gmail authentication failed. Please check your App Password."
    except Exception as e:
        logger.error(f"SMTP error | Type: {type(e).__name__}")
        return False, "Failed to send email. Please check network connectivity."

def is_valid_email(email):
    if not email or len(email) > 100 or '\n' in email or '\r' in email:
        return False
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email) is not None

# ==========================================
# STAGE 1: ONBOARDING
# ==========================================
def render_onboarding():
    st.markdown("<div style='height: 4vh;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="animate-entrance" style="text-align: center; margin-bottom: 2.5rem;">
                <div style="display: flex; justify-content: center; margin-bottom: 1.5rem;">
                    <div style="background: linear-gradient(135deg, #6366F1, #8B5CF6); border-radius: 16px; width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; color: white; font-size: 2rem; box-shadow: 0 8px 25px rgba(99,102,241,0.4);">
                        ✦
                    </div>
                </div>
                <h1 style="color: #111827; font-size: 2.5rem; font-weight: 700; margin: 0; letter-spacing: -0.02em;">StudySnap AI</h1>
                <p style="color: #6B7280; font-size: 1.1rem; margin-top: 0.5rem; margin-bottom: 0;">Snap it. Understand it. Master it.</p>
                <p style="color: #4B5563; font-weight: 500; margin-top: 4px;">Your AI-powered study companion</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card animate-entrance" style="padding: 32px; max-width: 560px; margin: 0 auto; position: relative;">', unsafe_allow_html=True)
        
        api_key = get_secret("GEMINI_API_KEY")
        
        if not api_key:
            st.markdown("""
                <div class="premium-error">
                    <div class="premium-error-title">⚠️ AI setup required</div>
                    <div class="premium-error-body">Add your Gemini API key to <code>.streamlit/secrets.toml</code><br>Then restart StudySnap AI.</div>
                </div>
            """, unsafe_allow_html=True)
            
        name = st.text_input("👤 Your Name", placeholder="e.g. Alex")
        email = st.text_input("✉️ Your Email", placeholder="alex@student.edu")
        
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        submit = st.button("Start Studying →", type="primary", use_container_width=True, disabled=not api_key)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if submit:
            if not name.strip() or not email.strip():
                show_error("Please provide both your name and email address.", "⚠️ Missing Info")
            elif len(name.strip()) > 50:
                show_error("Name is too long. Please use a shorter name.", "⚠️ Invalid Info")
            elif not is_valid_email(email.strip()):
                show_error("Please provide a valid email address.", "⚠️ Invalid Email")
            else:
                st.session_state.student_name = html.escape(name.strip())
                st.session_state.student_email = html.escape(email.strip())
                
                chat_session = init_chat_session()
                if chat_session:
                    st.session_state.gemini_chat = chat_session
                    st.session_state.onboarded = True
                    st.rerun()
                else:
                    show_error("Failed to initialize AI. Please check your API key.", "⚠️ Setup required")
                    
        st.markdown("""
            <div class="animate-entrance" style="display: flex; justify-content: center; gap: 1.5rem; margin-top: 2.5rem; color: #6B7280; font-size: 0.9rem; flex-wrap: wrap;">
                <span style="display: flex; align-items: center; gap: 6px;">📸 Notes</span>
                <span style="display: flex; align-items: center; gap: 6px;">💻 Code</span>
                <span style="display: flex; align-items: center; gap: 6px;">🧮 Math</span>
                <span style="display: flex; align-items: center; gap: 6px;">📝 Exams</span>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
            <div style="margin-bottom: 2rem;" class="animate-entrance">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <div style="background: linear-gradient(135deg, #6366F1, #8B5CF6); border-radius: 10px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; box-shadow: 0 4px 10px rgba(99,102,241,0.3);">
                        ✦
                    </div>
                    <h2 style="margin: 0; font-size: 1.25rem; font-weight: 700; color: #111827; letter-spacing: -0.02em;">StudySnap AI</h2>
                </div>
                <div style="color: #6B7280; font-size: 0.85rem; padding-left: 44px; line-height: 1.4; font-weight: 500;">
                    Snap it. Understand it.<br>Master it.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("＋ New Study Session", type="secondary", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.gemini_chat = init_chat_session()
            st.session_state.uploader_key += 1
            st.rerun()
            
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Determine summary eligibility
        has_meaningful_content = False
        has_ai_response = False
        for msg in st.session_state.chat_history:
            if not msg.get("is_hidden", False) and not msg.get("is_error", False):
                if msg["role"] == "user":
                    has_meaningful_content = True
                if msg["role"] == "model":
                    has_ai_response = True
        summary_eligible = has_meaningful_content and has_ai_response
        
        # Email Summary Card
        st.markdown("""
            <div class="glass-card animate-entrance" style="padding: 16px; margin-bottom: 12px;">
                <h4 style="margin-top: 0; margin-bottom: 6px; color: #111827; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
                    📧 Study Summary
                </h4>
                <div style="font-size: 0.8rem; color: #4B5563; margin-bottom: 12px; line-height: 1.4;">
                    Save today's learning directly to your inbox.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Send Summary", disabled=not summary_eligible, use_container_width=True, type="primary"):
            with st.spinner("Preparing summary..."):
                try:
                    conversation_text = ""
                    for msg in st.session_state.chat_history:
                        if msg.get("is_hidden", False) or msg.get("is_error", False):
                            continue
                        if msg["kind"] == "text":
                            role = "Student" if msg["role"] == "user" else "StudySnap AI"
                            conversation_text += f"{role}: {msg['content']}\n\n"
                            
                    final_prompt = f"Conversation History:\n{conversation_text}\n\n{prompts.SUMMARY_REQUEST_PROMPT}"
                    
                    client = get_gemini_client()
                    if not client:
                        show_error("Gemini is not configured. Add GEMINI_API_KEY to secrets.", "⚙️ Setup required")
                        return
                        
                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=final_prompt
                    )
                    
                    if response and hasattr(response, 'text') and response.text and response.text.strip():
                        summary_text = response.text
                        success, error_msg = send_summary_email(summary_text)
                        if success:
                            st.success("✓ Summary sent successfully.")
                            with st.expander("Preview"):
                                st.markdown(summary_text)
                        else:
                            show_error(error_msg, "📧 Email unavailable")
                    else:
                        show_error("Study summary could not be generated.", "⚠️ Gemini unavailable")
                except Exception as e:
                    show_error(handle_gemini_error(e), "⚠️ Gemini Error")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.container(border=True):
            safe_name = html.escape(st.session_state.student_name)
            safe_email = html.escape(st.session_state.student_email)
            st.markdown(f"**{safe_name}**<br><span style='font-size:0.85rem;color:#666;'>{safe_email}</span>", unsafe_allow_html=True)
            if st.button("Logout", use_container_width=True):
                for key in ["student_name", "student_email", "chat_history", "gemini_chat", "uploader_key", "onboarded", "last_request_time"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

# ==========================================
# MAIN WORKSPACE
# ==========================================
def render_header():
    api_key = get_secret("GEMINI_API_KEY")
    # Verify we actually have a working client
    client = None
    if api_key:
        try:
            client = get_gemini_client()
        except Exception:
            pass
            
    status_class = "configured" if client else ""
    status_text = "AI Ready" if client else "Setup Required"
    
    st.markdown(f"""
        <div class="app-header">
            <div class="header-brand">✦ StudySnap AI</div>
            <div class="header-status {status_class}">
                <span class="status-dot {status_class}"></span> {status_text}
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_empty_state():
    st.markdown("""
        <div class="animate-entrance" style="text-align: center; margin-top: 4rem; margin-bottom: 3rem;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">👋</div>
            <h2 style="color: #111827; font-size: 2rem; font-weight: 700; margin: 0; letter-spacing: -0.02em;">Welcome back!</h2>
            <p style="color: #6B7280; font-size: 1.1rem; margin-top: 0.5rem;">What are you learning today?</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="glass-card animate-entrance" style="text-align: center; padding: 1.5rem; color: #4B5563; margin-bottom: 1rem; font-weight: 500; transition: transform 200ms ease;">📸 Study Notes</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass-card animate-entrance" style="text-align: center; padding: 1.5rem; color: #4B5563; font-weight: 500; transition: transform 200ms ease; animation-delay: 50ms;">💻 Coding Problems</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="glass-card animate-entrance" style="text-align: center; padding: 1.5rem; color: #4B5563; margin-bottom: 1rem; font-weight: 500; transition: transform 200ms ease; animation-delay: 100ms;">📝 Exam Questions</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass-card animate-entrance" style="text-align: center; padding: 1.5rem; color: #4B5563; font-weight: 500; transition: transform 200ms ease; animation-delay: 150ms;">🧮 Math Problems</div>', unsafe_allow_html=True)
    
    st.markdown("<div class='animate-entrance' style='text-align: center; color: #9CA3AF; margin-top: 3rem; font-size: 0.95rem; animation-delay: 200ms;'>Attach your material or ask a question below.</div>", unsafe_allow_html=True)

def render_quick_actions():
    if not st.session_state.chat_history:
        return
        
    last_msg = st.session_state.chat_history[-1]
    if last_msg["role"] != "model" or last_msg.get("is_error", False):
        return
        
    st.markdown("<div class='animate-entrance' style='margin-top: 1rem; margin-bottom: 2.5rem; display: flex; gap: 10px; flex-wrap: wrap;'>", unsafe_allow_html=True)
    col1, col2, col3, _ = st.columns([2, 2, 2, 4])
    
    with col1:
        if st.button("✦ 5-Mark Answer", use_container_width=True, type="secondary"):
            handle_user_input("Please convert the previous explanation into a 5-mark exam-ready answer.", None, is_hidden=True)
    with col2:
        if st.button("⚡ Quick Revision", use_container_width=True, type="secondary"):
            handle_user_input("Give me a quick revision summary of this topic.", None, is_hidden=True)
    with col3:
        if st.button("📖 Explain Simpler", use_container_width=True, type="secondary"):
            handle_user_input("Can you explain this again using a simpler analogy?", None, is_hidden=True)
            
    st.markdown("</div>", unsafe_allow_html=True)

def handle_user_input(text, image_file, is_hidden=False):
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 1.5:
        show_error("Please wait a moment before sending another request.", "⚠️ Too Fast")
        st.stop()
    st.session_state.last_request_time = current_time

    if len(st.session_state.chat_history) > 50:
        show_error("Conversation limit reached. Please start a New Study Session.", "⚠️ History Limit")
        st.stop()
        
    contents_to_send = []
    
    # 1. Instantly display user input for this frame & add to history
    if image_file:
        if image_file.size > 10 * 1024 * 1024:
            show_error("Image is too large. Please upload an image below 10 MB.", "⚠️ Upload Error")
            st.session_state.uploader_key += 1
            st.rerun()
            
        try:
            image_bytes = image_file.getvalue()
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
            
            img = Image.open(io.BytesIO(image_bytes))
            img.thumbnail((2048, 2048)) 
            
            st.session_state.chat_history.append({"role": "user", "kind": "image", "content": img, "is_hidden": False})
            contents_to_send.append(img)
            with st.chat_message("user", avatar="🎓"):
                st.image(img, caption="Study Material Attached")
        except Exception:
            show_error("Invalid or corrupted image file. Please try another image.", "⚠️ Upload Error")
            st.session_state.uploader_key += 1
            st.rerun()
            
    if text:
        if len(text) > 2000:
            show_error("Your message is too long. Please shorten it.", "⚠️ Message Too Long")
            st.stop()
            
        st.session_state.chat_history.append({"role": "user", "kind": "text", "content": text, "is_hidden": is_hidden})
        contents_to_send.append(text)
        if not is_hidden:
            with st.chat_message("user", avatar="🎓"):
                st.markdown(text)
    elif image_file and not text:
        dp = "Analyze this study material and explain the important concepts clearly for a student."
        st.session_state.chat_history.append({"role": "user", "kind": "text", "content": dp, "is_hidden": True})
        contents_to_send.append(dp)

    # 2. Fetch Gemini Response
    with st.chat_message("model", avatar="🤖"):
        with st.spinner("Analyzing..."):
            try:
                chat = st.session_state.gemini_chat
                if not chat:
                    raise APIError("Gemini chat session not initialized.")
                    
                response = chat.send_message(contents_to_send)
                ai_text = response.text
                st.markdown(ai_text)
                st.session_state.chat_history.append({"role": "model", "kind": "text", "content": ai_text, "is_error": False})
            except Exception as e:
                error_msg = handle_gemini_error(e)
                show_error(error_msg, "⚠️ Gemini Error")
                st.session_state.chat_history.append({"role": "model", "kind": "text", "content": f"⚠️ {error_msg}", "is_error": True})
    
    # 3. Clean up and refresh
    st.session_state.uploader_key += 1
    st.rerun()

def render_chat_interface():
    render_sidebar()
    render_header()
    
    if len(st.session_state.chat_history) == 0:
        render_empty_state()
    else:
        for msg in st.session_state.chat_history:
            if msg.get("is_hidden", False):
                continue
            avatar = "🤖" if msg["role"] == "model" else "🎓"
            with st.chat_message(msg["role"], avatar=avatar):
                if msg["kind"] == "text":
                    st.markdown(msg["content"])
                elif msg["kind"] == "image":
                    st.image(msg["content"], caption="Study Material Attached")
                    
        render_quick_actions()

    # Premium Upload Area
    uploaded_image = st.file_uploader(
        "Upload", 
        type=["png", "jpg", "jpeg"],
        key=f"image_uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )
    
    analyze_img_btn = False
    if uploaded_image:
        safe_filename = html.escape(uploaded_image.name)
        st.markdown(f"""
            <div class="glass-card animate-entrance" style="padding: 16px; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-weight: 500; color: #111827; display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 1.2rem;">📎</span> {safe_filename}
                    </div>
                    <div style="font-size: 0.85rem; color: #059669; margin-top: 4px; font-weight: 500;">✓ Ready to analyze</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.image(uploaded_image, caption="Preview")
        
        if not st.session_state.chat_history:
            analyze_img_btn = st.button("Analyze Image Now", type="primary")

    user_text = st.chat_input("Ask StudySnap anything...")

    if user_text or analyze_img_btn:
        handle_user_input(user_text, uploaded_image)

# ==========================================
# APP ENTRY POINT
# ==========================================
def main():
    if not st.session_state.onboarded:
        render_onboarding()
    else:
        render_chat_interface()

if __name__ == "__main__":
    main()
