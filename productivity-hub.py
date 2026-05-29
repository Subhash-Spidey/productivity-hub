import streamlit as st 
from supabase import create_client
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
import uuid

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
signup_enabled = os.getenv("SIGNUP_ENABLED", "False").lower() == "true"


os.makedirs("./logs", exist_ok=True)

#create a logger object
logger = logging.getLogger("productivity hub")
logger.setLevel(logging.INFO)
logger.propagate = False


conn = create_client(url, key)

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
                    .select("user_id","user_name")\
                    .eq("user_name", username)\
                    .eq("password", password)\
                    .execute()\
                    .data
    except Exception as e:
        st.error("Server Error Occured, please try again later.")
        logger.exception(f"Error occured while validating user: {username}.")
        st.stop()
    
    if len(users) != 0:
        logger.info(f"{username} is a valid user.")
        st.session_state['current_user'] = users[0]['user_id']
        return True
    return False

def check_if_user_exists(conn, username):

    try:
        result = conn.table("users")\
                     .select('user_name')\
                     .eq('user_name', username)\
                     .execute()
        logger.info(f"user: {username} already exists" if len(result.data)!= 0 else f"user: {username} is a new user.")
    except Exception as e:
        st.error("Server Error, please try again later.")
        logger.exception(f"Error while checking if user: {username} already exists.")
        st.stop()
    
    if len(result.data):
        return True
    else:
        return False



def create_user(conn, username, password):
    
    try:
        unique_id = str(uuid.uuid4())
        createuser = conn.table("users")\
                    .insert({'user_id':unique_id,'user_name':username,'password':password})\
                    .execute()
        logger.info(f"sucessfully created user: {username}")
    except Exception as e:
        st.error("Server error occured, please try again later.")
        logger.exception(f"Error occured while creating user: {username}.")
        st.stop()
    
    if createuser.data:
        return True
    else:
        return False

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['logged_user'] = None

if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'login'

if 'message' not in st.session_state:
    st.session_state['message'] = None

if st.session_state['message']:
    st.success(st.session_state['message'])
    del st.session_state['message']
    
if not st.session_state['logged_in'] and st.session_state['current_page'] == 'login':

    with st.form("login-user"):
        login_user = st.text_input("Username", value='')
        login_pass = st.text_input("Password", value='', type='password')

        login_user = login_user.strip()
        login_pass = login_pass.strip()

        col1, col2 = st.columns([0.3,2.0])
        with col1:
            login_btn = st.form_submit_button("Login", type='primary', key='login')
        with col2:
            signup_btn = st.form_submit_button("Sign Up", key='signup')

            if signup_btn:
                if signup_enabled:
                    st.session_state['current_page'] = 'signup'
                    st.rerun()
                else:
                    st.error("Signup Disabled.")
                    st.session_state['current_page'] = 'login'
                    st.stop()

        if login_btn:
            logger.info(f"Received login request for user: {login_user} {', either username or password is empty' if not login_user or not login_pass else ''}")

            if not login_user or not login_pass:
                st.warning("Please enter username and password.")
                st.stop()
                
            try:
                valid = validate_user(conn, login_user, login_pass)
            except Exception as e:
                st.error("Server error occured, please try again later.")
                logger.exception(f"Error occured while creating connection and validating user: {login_user}.")
                st.stop()

            if valid:
                st.session_state['logged_in'] = True
                st.session_state['logged_user'] = login_user
                logger.info(f"login success for user: {login_user}")
                st.rerun()

            else:
                logger.info(f"login failed for user: {login_user}")
                st.error(f"login failed, please cross check credentials.")
            
elif st.session_state['current_page'] == 'signup' and signup_enabled:
    with st.form('signup-form'):
        username = st.text_input(label='Username', value='')
        password = st.text_input(label='Create password', value='', type='password')
        password_confirm = st.text_input(label='Confirm password', value='', type='password')    
        col1, col2 = st.columns([0.3,2.0])

        with col1:
            signup_btn1 = st.form_submit_button(label='SignUp',key='createaccount', type='primary')
        with col2:
            login_btn1 = st.form_submit_button("Login", key='login1')

        username = username.strip()
        password = password.strip()
        password_confirm = password_confirm.strip()

        if login_btn1:
            st.session_state['current_page'] = 'login'
            st.rerun()
        if signup_btn1:

            if len(username) == 0:
                st.error("Username cannot be empty.")
                st.stop()
            elif len(password) == 0 or len(password_confirm) == 0:
                st.error("Password cannot be empty")
                st.stop()
            
            if password != password_confirm:
                st.error("Passwords are not matching.")
                st.stop()
            else:
                try:

                    if check_if_user_exists(conn, username):
                        st.error("Unable to create account.")
                        st.stop() ##check this

                    valid = create_user(conn, username, password)

                except Exception as e:
                    st.error("Server error occured, please try again later.")
                    logger.exception(f"Error occured while creating user: {username}.")
                    st.stop()
                if valid:
                    st.session_state['current_page'] = 'login'
                    logger.info(f"Account created for user: {username}")
                    st.session_state['message'] = "Signup success!! Please Login"
                    st.rerun()

                else:
                    logger.info(f"signup failed for user: {username}")
                    st.error("Error creating account, please try again later")
            
else:
    st.success(f"Welcome {st.session_state['logged_user']} 👋")

    st.sidebar.success("🔓 Sidebar unlocked")

    if st.button("Logout"):
        logger.info(f"user: {st.session_state['logged_user']} logged out.")
        st.session_state['logged_in'] = False
        st.session_state['logged_user'] = None
        st.session_state['current_user'] = None

        st.rerun()