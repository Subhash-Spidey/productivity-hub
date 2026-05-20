import streamlit as st
import uuid
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

conn = create_client(url, key)

current_user = st.session_state.get('current_user')

if not current_user:
    st.error("Session expired. Please login again.")
    st.stop()

st.set_page_config(page_title="Notes",
                   page_icon="📝",
                   layout="centered",
                   initial_sidebar_state="auto")

if st.session_state.get('logged_in') == True:

    if 'note_edit_mode' not in st.session_state:
        st.session_state['note_edit_mode'] = False
    
    if 'note_to_edit' not in st.session_state:
        st.session_state['note_to_edit'] = None
    
    if 'message_note' in st.session_state:
        st.success(st.session_state['message_note'])
        del st.session_state['message_note']
    
    default_text = ''
    default_content = ''

    if st.session_state['note_edit_mode']:

        noteid_to_edit = st.session_state['note_to_edit']

        try:
            response = conn.table("notes")\
                                 .select("note_id", "title", "content")\
                                 .eq("note_id", noteid_to_edit)\
                                 .eq("user_id", current_user)\
                                 .eq('active', True)\
                                 .execute()\
            
            if response.data:
                edit_note = response.data[0]
            else:
                st.error("Note not found")
                st.stop()

        except Exception as e:
            st.error(f"Server error: {e}") 

        if len(edit_note) != 0:
            default_text = edit_note['title']
            default_content = edit_note['content']
              

    st.header("📝 Notes Page", text_alignment="center")
    st.subheader("📝 Notes", text_alignment="left")


    with st.form("notes_form"):

        title = st.text_input(label="Title", value=default_text)
        content = st.text_area(label="Content",value=default_content)

        add_note = st.form_submit_button("✏️ Update Note" if st.session_state['note_edit_mode'] else "➕ Add Note")

        if add_note:

            if len(title.strip()) == 0 or len(content.strip()) == 0:
                if len(title.strip()) == 0:
                    st.warning("Title cannot be empty.")
                if len(content.strip()) == 0:
                    st.warning("Content cannot be empty.")

            else:
                if st.session_state['note_edit_mode']:
                    
                    try:
                        update_note = conn.table('notes')\
                                         .update({'title':title, 'content':content})\
                                         .eq('note_id', st.session_state['note_to_edit'])\
                                         .eq('user_id', current_user)\
                                         .execute()
                    except:
                        st.error("Error while updating notes, Please Try again")
                        st.stop() 

                    st.session_state['message_note'] = "Note Updated."             

                else:    
                    unique_id = str(uuid.uuid4())

                    try:
                        add_notes = conn.table("notes")\
                                    .insert({'user_id':current_user, 'note_id':unique_id, 'title':title, 'content':content, 'active':True})\
                                    .execute()
                    except Exception as e:
                        st.error("Error while adding notes, Please Try again")
                        st.stop()

                    st.session_state['message_note'] = "Note Added."
                    

                st.session_state['note_to_edit'] = None
                st.session_state['note_edit_mode'] = False
                st.rerun() 


    with st.expander("📒 Your Notes"):

        try: 
            all_notes = conn.table("notes")\
                            .select('note_id','title', 'content')\
                            .eq('user_id', current_user)\
                            .eq('active', True)\
                            .execute()\
                            .data
        except Exception as e:
            st.error(f"Failed to load notes, please try again.{e}")
            st.stop()

        if len(all_notes) == 0:
            st.info("No notes yet. Add your first note above 👆")

        else:
            for note in all_notes:
                    
                    current_note = note['note_id']
                    
                    st.markdown(
                        f"""
                        <div style="
                            padding:15px;
                            border-radius:12px;
                            background-color:#f5f5f5;
                            color:black;
                            margin-bottom:10px;
                        ">
                            <b>📝 {note['title']}</b>
                            <br><br>
                            {note['content']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    col1, col2 = st.columns([1,1])
                    
                    #delete the note
                    del_btn = col1.button("❌ Delete",type='primary', key=f"c_{current_note}")

                    if del_btn:

                        try:
                            delete_note = conn.table('notes')\
                                              .update({'active': False})\
                                              .eq('note_id', current_note)\
                                              .eq('user_id', current_user)\
                                              .execute()
                        except Exception as e:
                            st.error(f"Unable to delete the note, please try again {e}")
                            st.stop()

                        st.session_state['message_note'] = "Note Deleted." 
                        st.session_state['note_to_edit'] = None
                        st.session_state['note_edit_mode'] = False

                        st.rerun()

                    #edit the note
                    edit_btn = col2.button("✏️ Edit", type='primary', key=f"e_{current_note}")

                    if edit_btn:
                        st.session_state['note_to_edit'] = current_note
                        st.session_state['note_edit_mode'] = True
                        st.rerun()

else:
    st.header("🔒 Please Login")
