import streamlit as st 
from supabase import create_client
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

os.makedirs("./logs", exist_ok=True)

#create a logger object
logger = logging.getLogger("productivity hub")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = RotatingFileHandler(filename='./logs/productivity_hub.log',
                                  maxBytes=1000000,
                                  backupCount=5)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)



st.set_page_config(page_title="Personal Knowledge Hub",
                   page_icon="🧠",
                   layout="centered",
                   initial_sidebar_state="auto")

st.header("🧠 Personal Knowledge Hub", text_alignment="center")


def validate_user(conn, username, password):

    try:
        users = conn.table("users")\
                    .select("*")\
                    .eq("user_name", username)\
                    .eq("password", password)\
                    .execute()\
                    .data
        logger.info(f"sucessfully received users data from 'users' table, users count {len(users)}.")
    except:
        st.error("Server Error Occured, please try again after sometime.")
        logger.exception("Error occured while getting users from table 'users'.")
        st.stop()
    
    if len(users) != 0:
        st.session_state['current_user'] = users[0]['user_id']
        return True
    return False

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['logged_user'] = None

if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

if not st.session_state['logged_in']:

    with st.form("login-user"):
        login_user = st.text_input("Username", value='')
        login_pass = st.text_input("Password", value='', type='password')
        btn = st.form_submit_button("Login")

        if btn:
            logger.info(f"Received login request for user: {login_user}")
            if not login_user.strip() or not login_pass.strip():
                st.warning("Please enter username and password")
                st.stop()
                
            try:
                conn = create_client(url, key)
                valid = validate_user(conn, login_user, login_pass)
            except Exception as e:
                st.error("Server Error Occured, please try again after sometime.")
                logger.exception(f"Error occured while creating connection and validating user: {login_user}.")
                st.stop()

            if valid:
                st.session_state['logged_in'] = True
                st.session_state['logged_user'] = login_user
                logger.info(f"login success for user: {login_user}")
                st.success("login success!! Sidebar unlocked")
                st.rerun()

            else:
                logger.info(f"login failed for user: {login_user}")
                st.error("login failed")
else:
    st.success(f"Welcome {st.session_state['logged_user']} 👋")

    st.sidebar.success("🔓 Sidebar unlocked")

    if st.button("Logout"):
        logger.info(f"user: {st.session_state['logged_user']} logged out.")
        st.session_state['logged_in'] = False
        st.session_state['logged_user'] = None
        st.session_state['current_user'] = None

        st.rerun()