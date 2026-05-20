import streamlit as st 
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

st.set_page_config(page_title="Personal Knowledge Hub",
                   page_icon="🧠",
                   layout="centered",
                   initial_sidebar_state="auto")

st.header("🧠 Personal Knowledge Hub", text_alignment="center")


def validate_user(conn, username, password):

    try:
        users = conn.table("users").select("*").eq("user_name", username).eq("password", password).execute()
        users = users.data
    except:
        st.error("Server Error, please try again.")
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

            if not login_user.strip() or not login_pass.strip():
                st.warning("Please enter username and password")
                st.stop()
                
            try:
                conn = create_client(url, key)
                valid = validate_user(conn, login_user, login_pass)
            except Exception as e:
                st.error("Server Error, please try again.")
                st.stop()

            if valid:
                st.session_state['logged_in'] = True
                st.session_state['logged_user'] = login_user
                st.success("login success!! Sidebar unlocked")
                st.rerun()

            else:
                st.error("login failed")
else:
    st.success(f"Welcome {st.session_state['logged_user']} 👋")

    st.sidebar.success("🔓 Sidebar unlocked")

    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['logged_user'] = None
        st.session_state['current_user'] = None
        st.rerun()