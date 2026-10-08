# StudySnap AI

Tagline:
"Snap it. Understand it. Master it."

## 1. Overview
StudySnap AI is an AI-powered multimodal study assistant. It helps students understand complex handwritten notes, textbook pages, coding problems, mathematics, and diagrams by uploading an image or asking a question, and receiving clear, structured AI-powered explanations.

## 2. Problem Statement
Students often struggle to understand:
- handwritten notes
- textbook pages
- diagrams
- coding problems
- mathematics
- exam questions

Traditional tools often fall short when interpreting images of physical study materials and lack interactive tutoring capabilities.

## 3. Solution
StudySnap AI lets students upload study material or ask questions and receive AI-powered explanations instantly, bridging the gap between static notes and interactive learning.

## 4. Key Features
- **Gemini Vision**: High-quality visual analysis of handwritten notes and printed material.
- **Multimodal study analysis**: Seamlessly handles text questions and image uploads together.
- **Conversational follow-up**: Chat with the AI about your material.
- **Quick Revision**: Instantly generates revision summaries of the current topic.
- **5-Mark Answer**: Formats complex concepts into concise, exam-ready answers.
- **Explain Simpler**: Breaks down complex topics using easier analogies.
- **Study Summary**: Generates a complete overview of the current session.
- **Gmail delivery**: Mails the session summary directly to your inbox.
- **Image validation**: Checks file size and type before processing.
- **Session management**: Safely scopes chat history to individual sessions.
- **Secure secrets**: Avoids exposing API keys to the frontend.
- **Prompt injection protection**: Guards against malicious inputs designed to extract internal rules.
- **Rate limiting**: Prevents abuse by limiting request frequencies.
- **Responsive UI**: A premium, "Liquid Glass" responsive web interface built on Streamlit.

## 5. How It Works
Student -> Study material / question -> StudySnap AI -> Gemini Vision / Chat -> Structured explanation -> Optional study summary -> Email

## 6. Technology Stack
- Python
- Streamlit
- Google Gemini API
- Pillow
- Gmail SMTP

## 7. Project Structure
- `app.py`: Main Streamlit application logic and UI.
- `prompts.py`: System prompts, security rules, and structural guidelines for the AI model.
- `requirements.txt`: Runtime dependencies required to run the application.
- `.streamlit/secrets.toml.example`: Example configuration for API keys and credentials.
- `.gitignore`: Files excluded from source control.

## 8. Local Setup
Use the following commands to set up the project locally:

```bash
python -m venv venv
# On Windows: .\venv\Scripts\Activate.ps1
# On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## 9. Environment / Streamlit Secrets Setup
You must configure the API keys locally for the application to work.
Create a `.streamlit` folder and a `secrets.toml` file inside it containing:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
GMAIL_ADDRESS = "your_gmail_address_here"
GMAIL_APP_PASSWORD = "your_16_character_app_password_here"
```

**IMPORTANT**: NEVER put real secrets in GitHub. Add your `secrets.toml` to `.gitignore`.

## 10. Running the Application
```bash
streamlit run app.py
```

## 11. GitHub Deployment
This repository is configured to exclude local secrets and environments. Ensure you do not accidentally commit `.streamlit/secrets.toml`. 

## 12. Streamlit Community Cloud Deployment
This project is fully ready for Streamlit Community Cloud. 
1. Connect your GitHub repository to Streamlit Community Cloud.
2. In the deployment dashboard, go to "Advanced Settings" > "Secrets".
3. Paste the contents of your `secrets.toml` into the secrets field.

## 13. Security
This application includes essential security measures for safe local and community deployment:
- secrets excluded from source code
- input validation on text fields
- image size limits (max 10MB) to prevent memory exhaustion
- email validation
- HTML escaping for user inputs to prevent XSS
- prompt injection defenses inside the system prompt
- rate limiting on chat submissions
- safe logging of API errors
- no shell execution or direct OS access

*Note: This is a standalone Streamlit app and does not feature enterprise-grade centralized authentication.*

## 14. Limitations
- Streamlit session state is temporary. Chat history is lost on refresh or restart.
- No persistent database for long-term account data.
- No centralized authentication (uses simple name/email scoping).
- No global IP rate limiter.
- Gmail SMTP requires a 16-character Google App Password.
- Gemini API requires a valid API access key with quota.

## 15. Future Improvements
- Add persistent database storage for accounts and chat histories.
- Implement robust multi-user authentication (e.g., OAuth).
- Add support for PDF document parsing.
