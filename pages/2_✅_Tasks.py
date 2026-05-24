import streamlit as st
from datetime import datetime, date
import uuid
from supabase import create_client
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

logger = logging.getLogger("Tasks")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = RotatingFileHandler(filename="./logs/tasks.log",
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

st.set_page_config(page_title="Tasks",
                   page_icon="✅",
                   layout="centered",
                   initial_sidebar_state="auto")

if st.session_state.get('logged_in') == True:

    if 'task_to_edit' not in st.session_state:
        st.session_state['task_to_edit'] = None

    if 'task_edit_mode' not in st.session_state:
        st.session_state['task_edit_mode'] = False
    
    if 'message_task' in st.session_state:
        st.success(st.session_state['message_task'])
        del st.session_state['message_task']
    
    default_task=''
    default_date = datetime.now().date()

    if st.session_state['task_edit_mode']:

        taskid_to_edit = st.session_state['task_to_edit']

        try:
            response = conn.table('tasks')\
                .select('task_name', 'due_date')\
                .eq('task_id', taskid_to_edit)\
                .eq('user_id', current_user)\
                .eq('active', True)\
                .execute()\
            
            logger.info(f"Successfully retrieved task: {taskid_to_edit} from table 'tasks' to edit, count {len(response.data)}")
                
            
            if response.data:
                edit_task = response.data[0]
            else:
                st.error("Task not found.")
                st.stop()
        except Exception as e:
            st.error(f"Server error occurred, please try again later") 
            logger.exception(f"Failed to retrieve task: {taskid_to_edit} from table 'tasks' to edit.")
            st.stop()
        
        if len(edit_task):
            default_task = edit_task['task_name']
            default_date = edit_task['due_date']
    
        
    st.header("✅ TO-DO PAGE", text_alignment="center")
    st.subheader("✅ Tasks", text_alignment="left")

    with st.form(key='tasks_key'):

        task = st.text_input("Task Name", value=default_task)

        due_date = st.date_input("Due Date",value=default_date)

        add_task = st.form_submit_button("✏️ Update Task" if st.session_state['task_edit_mode'] else "➕ Add Task")

        if add_task:

            logging.info(f"User: {current_user} submitted a task.")

            if len(task.strip()) ==0:
                st.warning("Task cannot be empty.")
                logger.info(f"failed to add a task for user: {current_user}, task is empty.")

            else:

                if st.session_state['task_edit_mode']:

                    logger.info(f"Received request for user: {current_user} to edit a task.")

                    try:
                        update_task = conn.table("tasks")\
                                       .update({'task_name':task, 'due_date':due_date.isoformat()})\
                                       .eq('task_id', st.session_state['task_to_edit'])\
                                       .eq('user_id', current_user)\
                                       .execute()
                        logger.info(f"Task update is success for user: {current_user}, task_id: {st.session_state['task_to_edit']}")
                    except Exception as e:
                        st.error("Error while updating task, Please Try again later.")
                        logger.exception(f"Failed to update task for user: {current_user}, task_id: {st.session_state['task_to_edit']}")
                        st.stop()

                    st.session_state['message_task'] = "Task Updated."  
                    st.session_state['task_edit_mode'] = False
                    st.session_state['task_to_edit'] = None
                
                else:     
                    task_id = str(uuid.uuid4())
                    logger.info(f"Received request for user: {current_user} to add a task.")

                    try:
                        new_task = conn.table("tasks")\
                                       .insert({'user_id':current_user, 'task_id':task_id, 'task_name':task, 'due_date':due_date.isoformat(), 'completion_date':None, 'active':True})\
                                       .execute()
                        logger.info(f"Successfully added task for user {current_user} to 'tasks' table.")
                    except Exception as e:
                        st.error(f"Error while adding task, please try again later.")
                        logger.Exception(f"Failed to add task for user:{current_user}")
                        st.stop()
                    st.session_state['message_task'] = "Task Added."
                st.rerun()


    #display tasks
    with st.expander("📋 Your Tasks"):

        try:
            all_tasks = []
            all_tasks = conn.table("tasks")\
                            .select('user_id', 'task_id', 'task_name','due_date')\
                            .eq('user_id',current_user)\
                            .eq('active', True)\
                            .is_('completion_date', None)\
                            .order('due_date', desc=False)\
                            .execute()\
                            .data
            logger.info(f"Successfully retrieved all tasks for user: {current_user} to display, count {len(all_tasks)}")
        except Exception as e:
            st.error(f"Failed to load tasks, please try again later.")
            logger.exception(f"Failed to load tasks from table 'tasks' for user: {current_user}.")
            st.stop()

        if len(all_tasks) == 0:
            st.info("No tasks yet. Add your first task above 👆")
            logger.info("No tasks to display for user: {current_user}")

        else:

            for task in all_tasks:

                current_task = task['task_id']

                st.markdown(
                    f"""
                    <div style="
                        padding:15px;
                        border-radius:12px;
                        background-color:#f5f5f5;
                        color:black;
                        margin-bottom:10px;
                    ">
                        <b>📅Task: {task['task_name']}</b> 
                        <br><br>
                        Due Date: {task['due_date']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                col1, col2, col3 = st.columns([1,1,1])


                #mark as completed
                completed_add_task = col1.button("✅ Completed",type='primary', key=f"c_{current_task}")

                if completed_add_task:
                    logger.info(f"Received a request to mark task: {current_task} as complete for user: {current_user} ")

                    completion_date = datetime.now().date()
                    
                    try:
                        mark_complete = conn.table("tasks")\
                            .update({'completion_date':completion_date.isoformat()})\
                            .eq('task_id', current_task)\
                            .eq('user_id', current_user)\
                            .execute()
                        logger.info(f"Completed task: {current_task} for user: {current_user}")
                        
                    except Exception as e:
                        st.error(f"Error while marking the task as complete, please try again later.")
                        logger.exception(f"failed to mark task: {current_task} as complete for user: {current_user} from table 'tasks'.")
                        st.stop()

                    st.session_state['message_task'] = "Yay!! you have completed a Task."
                    st.session_state['task_edit_mode'] = False
                    st.rerun()


                #delete the task
                del_btn = col2.button("❌ Delete", type='primary' ,key=f"d_{current_task}")

                if del_btn:
                    logger.info(f"Received a request to delete task: {current_task} for user: {current_user} ")
                    try:
                        delete_task = conn.table("tasks")\
                            .update({'active':False})\
                            .eq('task_id', current_task)\
                            .eq('user_id', current_user)\
                            .execute()
                        logger.info(f"Deleted task: {current_task} for user: {current_user}")
                    except Exception as e:
                        st.error(f"Failed to delete the task, please try again later")
                        logger.exception(f"failed to delete task: {current_task} for user: {current_user} from table 'tasks'")
                            
                        st.stop()

                    st.session_state['message_task'] = "Task Deleted."
                    st.session_state['task_edit_mode'] = False
                    st.rerun()

                #edit the task
                edit_add_task = col3.button("✏️ Edit", type='primary', key=f"e_{current_task}")

                if edit_add_task:
                        st.session_state['task_to_edit'] = current_task
                        st.session_state['task_edit_mode'] = True
                        st.rerun()


    ###Completed tasks
    with st.expander("✅ Completed Tasks", expanded=False):

        try:
            completed_tasks = conn.table("tasks")\
                            .select('task_name','due_date', 'completion_date')\
                            .eq('user_id',current_user)\
                            .eq('active', True)\
                            .not_.is_('completion_date', None)\
                            .order('completion_date', desc=True)\
                            .execute()\
                            .data
            logger.info(f"Successfully retrieved completed tasks for user: {current_user}, count: {len(completed_tasks)}")
        except Exception as e:
            st.error(f"Error while retrieving the completed tasks, please try again later")
            logger.exception(f"Failed to retrieve completed tasks for user: {current_user}")


        if len(completed_tasks) == 0:
            st.markdown("### 📚 No tasks completed yet")
            logger.info(f"User: {current_task} haven't completed any tasks yet.")

        else:
            for task in completed_tasks:

                completed_at = date.fromisoformat(task['completion_date'])
                due = date.fromisoformat(task['due_date'])
                days_diff = (completed_at - due).days

                # 🎨 color logic
                if days_diff > 5:
                    border_color = "#ff4b4b"   # red
                    status = f"⏳ {days_diff} day(s) after due date"
                elif days_diff > 2:
                    border_color = "#ffa500"   # orange
                    status = f"⏳ {days_diff} day(s) after due date"
                elif days_diff < 0:
                    border_color = "#F8C8DC"
                    days_diff = -days_diff
                    status = f"⏳ {days_diff} day(s) before due date"
                    
                else:
                    border_color = "#4CAF50"   # green
                    status = f"⏳ {days_diff} day(s) after due date"

                st.markdown(f"""
                <div style="
                    background-color: var(--secondary-background-color);
                    padding:14px;
                    border-radius:10px;
                    margin-bottom:10px;
                    border-left:4px solid {border_color};
                ">
                    <div style="font-size:16px; font-weight:600;">
                        ✔️ {task['task_name']}
                    </div>
                    <div style="font-size:13px; margin-top:4px; color:gray;">
                        📅 Due: <b>{task['due_date']}</b>
                    </div>
                    <div style="font-size:13px; margin-top:2px;">
                        ✅ Completed: {completed_at.strftime("%Y-%m-%d")}
                    </div>
                    <div style="font-size:12px; color:gray;">
                        {status}
                    </div>
                </div>
                """, unsafe_allow_html=True)

else:
    st.header("🔒 Please Login")

