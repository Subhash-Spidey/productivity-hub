import streamlit as st
import uuid
from datetime import datetime, date
from supabase import create_client
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler


load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

logger = logging.getLogger("Journals")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = RotatingFileHandler(filename='./logs/journals.log',
                                  maxBytes=1000000,
                                  backupCount=5)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)

conn = create_client(url, key)

current_user = st.session_state.get('current_user')

if not current_user:
    st.error("Session expired. Please login again.")
    st.stop()

#set the page layout
st.set_page_config(page_title='Journal',
                   page_icon='📖',
                   layout='centered',
                   initial_sidebar_state='auto')

#if user logged in
if st.session_state.get('logged_in') == True:

    #if editing enable this
    if 'edit_mode_journal' not in st.session_state:
        st.session_state['edit_mode_journal'] = False
    
    #entry index to edit
    if 'journal_to_edit' not in st.session_state:
        st.session_state['journal_to_edit'] = None
    
    if 'message_journal' in st.session_state:
        st.success(st.session_state['message_journal'])
        del st.session_state['message_journal']
    
    moods = ['😊Happy', '😢Sad', '😐Neutral']

    default_text = ""
    default_date = datetime.now().today()
    default_mood = None

    if st.session_state['edit_mode_journal']:
        journalid_to_edit = st.session_state['journal_to_edit']

        try:
            response = conn.table("journals")\
                               .select('journal_text', 'journal_date', 'mood')\
                               .eq('journal_id', journalid_to_edit)\
                               .eq('user_id', current_user)\
                               .eq('active', True)\
                               .execute()
            logger.info(f"Successfully retrieved journal: {journalid_to_edit} from table 'journals' to edit, count {len(response.data)}")
                               
            if response.data:
                edit_journal = response.data[0]
            else:
                st.error("Journal not found")
                st.stop()
            
        except Exception as e:
            st.error(f"Server error occurred, please try again later") 
            logger.exception(f"Failed to retrieve journal: {journalid_to_edit} from table 'journals' to edit.")
            st.stop()
        

        if len(edit_journal) != 0:
            default_text = edit_journal['journal_text']
            default_date = date.fromisoformat(edit_journal['journal_date'])
            default_mood = moods.index(edit_journal['mood'])

    st.header("📖 Journals Page", text_alignment="center")
    st.subheader("📖 Journals", text_alignment="left")

        


    with st.form('journal-form'):

        text = st.text_area("Journal", value=default_text)
        journal_date = st.date_input("Date", value=default_date)
        mood = st.radio('Select Mood',options=moods, index=default_mood, horizontal=True)

        #modify button text according to the action
        btn = st.form_submit_button("✏️ Update Journal" if st.session_state['edit_mode_journal'] else "➕ Add Journal" )

        if btn:

            #validations
            if len(text.strip()) == 0:
                st.error("Please add the Journal.")
                logger.info(f"failed to add a journal for user: {current_user}, text is empty.")

            elif not(mood):
                st.error("Please select a Mood.")  
                logger.info(f"failed to add a journal for user: {current_user}, mood not selected.") 
            
            
            else:
                #edit mode
                if st.session_state['edit_mode_journal']:
                    logger.info(f"Received request for user: {current_user} to edit a journal.")

                    try:
                        upd_journal = conn.table("journals")\
                                       .update({'journal_text':text, 'journal_date':journal_date.isoformat(),'mood':mood})\
                                       .eq('journal_id', st.session_state['journal_to_edit'])\
                                       .eq('user_id', current_user)\
                                       .execute()
                        logger.info(f"Journal update is success for user: {current_user}, journal_id: {st.session_state['journal_to_edit']}")
                    except Exception as e:
                        st.error("Error while updating journal, Please Try again later")
                        logger.exception(f"Failed to update journal for user: {current_user}, journal_id: {st.session_state['journal_to_edit']}")
                        
                        st.error()
                    
                    st.session_state['message_journal'] = 'Journal Updated.'
                    st.session_state['edit_mode_journal'] = False
                    st.session_state['journal_to_edit'] = None
                
                #add mode
                else:
                    journal_id = str(uuid.uuid4())
                    logger.info(f"Received request for user: {current_user} to add a journal.")

                    try:
                        add_journal = conn.table('journals')\
                                        .insert({'user_id':current_user,'journal_id':journal_id,'journal_text':text, 'journal_date':journal_date.isoformat(), 'mood':mood, 'active':True})\
                                        .execute()
                        logger.info(f"Successfully added journal for user: {current_user} to 'journals' table.")
                    except Exception as e:
                        st.error("Error while adding journal, Please Try again later")
                        logger.Exception(f"Failed to add journal for user: {current_user}")
                        st.stop()

                    st.session_state['message_journal'] = 'Journal Added.'
                st.rerun()

    #validations for displaying journals
    with st.expander("📖 Your Journals"):

        try:
            all_journals = []
            all_journals = conn.table("journals")\
                               .select('journal_id', 'journal_text', 'journal_date', 'mood')\
                               .eq('user_id', current_user)\
                               .eq('active', True)\
                               .order('journal_date', desc=True)\
                               .execute()\
                               .data
            logger.info(f"Successfully retrieved all journals for user: {current_user} to display, count {len(all_journals)}")
        except:
            st.error(f"Failed to load journals, please try again later")
            logger.exception(f"Failed to load journals from table 'journals' for user: {current_user}.")
            st.stop()

        if len(all_journals) == 0:
            st.info("No journals yet. Add your first journal above 👆")
            logger.info("No journals to display for user: {current_user}")
        

        #if journals exist
        else:
            
            for journal in all_journals:

                current_journal = journal['journal_id']

                #displaying journals
                st.markdown(
                    f"""
                    <div style="
                        padding:15px;
                        border-radius:12px;
                        background-color:#f5f5f5;
                        color:black;
                        margin-bottom:10px;
                    ">
                        <b>📅 {journal['journal_date']}</b> | <b>{journal['mood']}</b>
                        <br><br>
                        {journal['journal_text']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                col1, col2 = st.columns([1,1])

                #deleting a journal
                with col1:
                    if col1.button(f"❌ Delete Journal", type="primary", key=f"d_{current_journal}"):
                        logger.info(f"Received a request to delete journal: {current_journal} for user: {current_user} ")
                        try:
                            del_journal = conn.table('journals')\
                                              .update({'active':False})\
                                              .eq('journal_id', current_journal)\
                                              .eq('user_id', current_user)\
                                              .execute()
                            logger.info(f"Deleted journal: {current_journal} for user: {current_user}")
                        except Exception as e:
                            st.error(f"Failed to delete the journal, please try again later")
                            logger.exception(f"failed to delete journal: {current_journal} for user: {current_user} from table 'journals'")
                            st.error()
                        
                        st.session_state['message_journal'] = 'Journal Deleted.'
                        st.session_state['journal_to_edit'] = None
                        st.session_state['edit_mode_journal'] = False
                        st.rerun()
                
                #editing a journal -
                with col2: 
                    if col2.button(f"✏️ Edit Journal", type="primary", key=f"e_{current_journal}"):
                        st.session_state['journal_to_edit'] = current_journal
                        st.session_state['edit_mode_journal'] = True
                        st.rerun()

                        
else:
    st.header("🔒 Please Login")