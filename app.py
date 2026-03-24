import streamlit as st
import joblib
import hashlib
from PIL import Image
import pytesseract
import os
import re
import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
from supabase import create_client, Client # Added for Supabase

# --- CONFIGURATION ---
# Note: For Streamlit Cloud deployment, remove the local tesseract path line.
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="Smart Email Classifier", page_icon="🤖", layout="centered")

# --- SUPABASE CONNECTION ---
# These will be set in Streamlit Cloud Secrets
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# --- DATABASE LOGIC (SUPABASE) ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def add_userdata(fullname, username, password):
    # Inserts data into Supabase cloud table
    data = {"fullname": fullname, "username": username, "password": password}
    supabase.table("userstable").insert(data).execute()

def login_user(username, password):
    # Checks data from Supabase cloud table
    response = supabase.table("userstable").select("fullname").eq("username", username).eq("password", password).execute()
    if response.data:
        return [response.data[0]['fullname']]
    return None

# --- CUSTOM CSS ---
st.markdown("""
<style>
.stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #4CAF50; color: white; font-weight: bold; border: none; }
.stButton>button:hover { background-color: #45a049; box-shadow: 0px 4px 8px rgba(0,0,0,0.2); }
.prediction-card{ padding:30px; border-radius:15px; background-color:#f8f9fa; border-top:5px solid #4CAF50; text-align:center; box-shadow:0px 4px 12px rgba(0,0,0,0.1); color:black;}
.spam-alert{ padding:30px; border-radius:15px; background-color:#ffe6e6; border-top:6px solid red; text-align:center; box-shadow:0px 4px 12px rgba(0,0,0,0.4); color:black; }
.header-style{ text-align:center; color:#2E4053; margin-bottom:5px; }
.info-box { background-color: #e8f0fe; padding: 15px; border-radius: 8px; border-left: 5px solid #1a73e8; margin: 10px 0 20px 0; }
</style>
""", unsafe_allow_html=True)

# --- GMAIL FETCH LOGIC ---
def fetch_gmail_emails_app_pass(user_email, app_password):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user_email, app_password)
        mail.select("inbox")
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        latest_10_ids = email_ids[-10:][::-1]
        subjects = []
        bodies = {}
        for e_id in latest_10_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject_header = decode_header(msg["Subject"])[0]
                    subject = subject_header[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(subject_header[1] if subject_header[1] else "utf-8")
                    sender = msg.get("From")
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors='ignore')
                    soup = BeautifulSoup(body, "html.parser")
                    clean_text = soup.get_text(separator='\n')
                    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                    subjects.append(subject)
                    bodies[subject] = {"from": sender, "body": clean_text}
        mail.logout()
        return subjects, bodies
    except Exception as e:
        st.error(f"Login failed! Please check your App Password. Error: {e}")
        return [], {}

def main():
    # Session state for login
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        st.markdown("<h1 class='header-style'>🔐 AI Email Classifier Access</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            user = st.text_input("Username (Email)", key="l_user")
            passwd = st.text_input("Password", type='password', key="l_pass")
            if st.button("Login"):
                result = login_user(user, make_hashes(passwd))
                if result:
                    st.session_state['logged_in'] = True
                    st.session_state['user_fullname'] = result[0]
                    st.rerun()
                else: st.error("Invalid Username or Password!")
        with tab2:
            new_fullname = st.text_input("Full Name", key="r_name")
            new_user = st.text_input("Username (Email)", key="r_user")
            new_passwd = st.text_input("Create Password", type='password', key="r_pass")
            if st.button("Register Account"):
                if new_fullname and new_user and new_passwd:
                    # Password Strength Validation (Symbols & Numbers)
                    if len(new_passwd) < 8 or not re.search("[0-9]", new_passwd) or not re.search("[@#$%^&+=]", new_passwd):
                        st.warning("Password must be 8+ chars with at least one number and one symbol (@#$%^&+=).")
                    else:
                        add_userdata(new_fullname, new_user, make_hashes(new_passwd))
                        st.success("Account created successfully! Please Login.")
    else:
        with st.sidebar:
            st.title(f"Welcome, {st.session_state['user_fullname']}! 👋")
            if st.button("Logout"):
                st.session_state['logged_in'] = False
                st.rerun()

        st.markdown("<h1 class='header-style'>📧 Smart Email Classifier</h1>", unsafe_allow_html=True)
        option = st.radio("Select Input Method:", ("Type Email Content", "Image (OCR)", "Fetch from Gmail"))
        
        final_text = ""

        if option == "Type Email Content":
            final_text = st.text_area("Paste Email Body:", placeholder="Example: Win $1000 prize...")
        
        elif option == "Image (OCR)":
            uploaded_file = st.file_uploader("Upload screenshot:", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                img = Image.open(uploaded_file)
                st.image(img, use_container_width=True)
                final_text = pytesseract.image_to_string(img)
                st.text_area("Extracted Text:", final_text)
        
        else:
            st.subheader("Fetch Emails from Gmail")
            target_email = st.text_input("Gmail Address:", placeholder="yourname@gmail.com")
            app_pass = st.text_input("App Password:", type="password", placeholder="xxxx xxxx xxxx xxxx")
            
            st.markdown("""
                <div class="info-box">
                    <strong>💡 How to get App Password?</strong><br>
                    1. Go to your <b>Google Account Settings</b>.<br>
                    2. Enable <b>2-Step Verification</b>.<br>
                    3. Search for <b>'App Passwords'</b> in the search bar.<br>
                    4. Select 'Other' and name it 'Email Classifier'.<br>
                    5. Copy the 16-digit yellow box code and paste it above.
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Fetch Latest Emails"):
                if target_email and app_pass:
                    with st.spinner("Connecting to Gmail..."):
                        subjects, bodies = fetch_gmail_emails_app_pass(target_email, app_pass)
                        st.session_state["subjects"] = subjects
                        st.session_state["bodies"] = bodies
                else:
                    st.warning("Please enter your Gmail and App Password.")

            if "subjects" in st.session_state and len(st.session_state["subjects"]) > 0:
                selected_email = st.selectbox("Select Email to Classify", st.session_state["subjects"])
                email_data = st.session_state["bodies"][selected_email]
                final_text = email_data['body']

                st.markdown(f"""
                <div style="background-color: white; padding: 25px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <h3 style="color:#1a73e8;">{selected_email}</h3>
                    <p><b>From:</b> {email_data['from']}</p>
                    <hr>
                    <p style='white-space: pre-line;'>{final_text}</p>
                </div>
                """, unsafe_allow_html=True)

        if st.button("Categorize Your Email ✨"):
            if final_text.strip():
                try:
                    model = joblib.load('email_classifier_model.pkl')
                    prediction = model.predict([final_text])[0]
                    if prediction.lower() == "spam":
                        st.markdown('<div class="spam-alert"><h2>⚠ ALERT: SPAM DETECTED</h2></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="prediction-card"><h1>{prediction.upper()}</h1></div>', unsafe_allow_html=True)
                        st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please provide content first!")

if __name__ == '__main__':
    main()