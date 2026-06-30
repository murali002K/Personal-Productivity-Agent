import streamlit as st
import requests
import pandas as pd

# Global API URL configuration for consistency
BASE_URL = "https://personal-productivity-agent.onrender.com"

st.set_page_config(
    page_title="Personal Productivity Agent",
    page_icon="📋",
    layout="wide"
)

st.title("Personal Productivity Agent")
st.sidebar.title("📋 Navigation")
page = st.sidebar.radio(
    "Go To",
    [
        "📊 Dashboard",
        "✅ Tasks",
        "📈 Reports"
    ]
)

# ==============================================================================
# 📊 DASHBOARD PAGE
# ==============================================================================
if page == "📊 Dashboard":
    st.header("Dashboard")
    st.write("Welcome to Dashboard")
    try:
        tasks = requests.get(f"{BASE_URL}/tasks").json()
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("status") == "Completed"])
        pending_tasks = len([t for t in tasks if t.get("status") == "Pending"])
        overdue = len([t for t in tasks if t.get("status") == "Overdue"])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Tasks", total_tasks)
        c2.metric("Completed", completed_tasks)
        c3.metric("Pending", pending_tasks)
        c4.metric("Overdue", overdue)
        
        df = pd.DataFrame(tasks)
        
        if not df.empty:
            st.subheader("Recent Tasks")
            st.dataframe(
                df,
                use_container_width=True
            )
            
            # --- Quick Complete Action Section ---
            st.subheader("Quick Complete")
            has_pending = False
            for task in tasks:
                if task.get("status") == "Pending":
                    has_pending = True
                    col1, col2 = st.columns([4, 1])
                    col1.write(task.get("title"))
                    if col2.button("Complete", key=f"dashboard_{task.get('id')}"):
                        requests.put(f"{BASE_URL}/tasks/{task.get('id')}")
                        st.rerun()
            if not has_pending:
                st.success("No pending tasks left to complete!")
            
            st.subheader("Priority Distribution")
            if "priority" in df.columns:
                priority_counts = df["priority"].value_counts()
                st.bar_chart(priority_counts)
        else:
            st.info("No task records available to display charts.")
        
        st.subheader("Status Summary Breakdown")
        chart_data = pd.DataFrame({
            "Status": ["Completed", "Pending"],
            "Count": [completed_tasks, pending_tasks]
        })
        st.bar_chart(chart_data.set_index("Status"))
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
        st.progress(completion_rate / 100)
    except Exception as e:
        st.error(f"Could not connect to backend server: {e}")

# ==============================================================================
# ✅ TASKS PAGE
# ==============================================================================
elif page == "✅ Tasks":
    st.header("✅ Task Management")
    
    # --- Form Section to Create Tasks ---
    st.subheader("➕ Create New Task")
    title = st.text_input("Task Title", key="new_task_title")
    category = st.selectbox("Category", ["Learning", "Work", "Health", "Personal"])
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])       
    due_date = st.date_input("Due Date")
    
    if st.button("Create Task"):
        if title:
            try:
                response = requests.post(
                    f"{BASE_URL}/tasks",
                    json={
                        "title": title,
                        "category": category,
                        "priority": priority,
                        "due_date": str(due_date)
                    }
                )
                if response.status_code == 200:
                    st.success("Task Created Successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")
        else:
            st.warning("Please provide a task title.")

    st.markdown("---")

    # --- View, Complete & Delete Actions Section ---
    try:
        tasks = requests.get(f"{BASE_URL}/tasks").json()
        
        st.subheader("All Tasks")
        df = pd.DataFrame(tasks)
        if not df.empty:
            st.dataframe(df)
            
            high_priority = len([t for t in tasks if t.get("priority") == "High"])
            st.metric("High Priority Tasks", high_priority)
            
            st.subheader("Manage Tasks")
            for task in tasks:
                # 3-column layout for uniform alignment: Meta data (4), Complete (1), Delete (1)
                col1, col2, col3 = st.columns([4, 1, 1])
                
                # Highlight completed tasks visually with a checkmark and crossout decoration
                if task.get("status") == "Completed":
                    col1.write(f"✅ ~~**{task.get('title')}** ({task.get('priority')} Priority)~~")
                    # Render disabled placeholder button to maintain grid alignment
                    col2.button("Done", key=f"done_{task.get('id')}", disabled=True)
                else:
                    col1.write(f"**{task.get('title')}** ({task.get('priority')} Priority)")
                    # Show active Complete button only if task is pending
                    if col2.button("Complete", key=f"complete_{task.get('id')}"):
                        requests.put(f"{BASE_URL}/tasks/{task.get('id')}")
                        st.rerun()
                
                # Delete action button is always rendered on the layout row
                if col3.button("Delete", key=f"delete_{task.get('id')}"):
                    requests.delete(f"{BASE_URL}/tasks/{task.get('id')}")
                    st.rerun()
        else:
            st.info("No tasks found.")
            
    except Exception as e:
        st.error(f"Could not load tasks from server: {e}")

# ==============================================================================
# 📈 REPORTS PAGE
# ==============================================================================
elif page == "📈 Reports":
    st.header("📈 Reports & Insights")
    
    # --- Morning Check-in ---
    st.subheader("🌤️ Morning Check-in")
    morning_note = st.text_area("What are you planning today?", key="morning_input")
    if st.button("Save Morning Check-in"):
        try:
            response = requests.post(f"{BASE_URL}/checkin/morning", json={"morning_notes": morning_note})
            st.success(response.json().get("message", "Morning check-in saved successfully!"))
        except Exception as e:
            st.error(f"Error: {e}")
            
    # --- Evening Check-in ---
    st.subheader("🌙 Evening Check-in")
    evening_note = st.text_area("What did you complete today?", key="evening_input")
    if st.button("Save Evening Check-in"):
        try:
            response = requests.post(f"{BASE_URL}/checkin/evening", json={"evening_notes": evening_note})
            st.success(response.json().get("message", "Evening check-in saved successfully!"))
        except Exception as e:
            st.error(f"Error: {e}")

    # --- Overdue Tasks ---
    st.subheader("⚠️ Overdue Tasks")
    if st.button("Show Overdue Tasks"):
        try:
            response = requests.get(f"{BASE_URL}/overdue-tasks").json()
            if isinstance(response, list) and len(response) > 0:
                st.warning(f"You have {len(response)} overdue tasks!")
                st.dataframe(pd.DataFrame(response), use_container_width=True)
            elif isinstance(response, dict) and "overdue_tasks" in response:
                tasks_list = response["overdue_tasks"]
                st.warning(f"You have {len(tasks_list)} overdue tasks!")
                st.dataframe(pd.DataFrame(tasks_list), use_container_width=True)
            else:
                st.success("Great job! No overdue tasks found.")
        except Exception as e:
            st.error(f"Error: {e}")

    # --- Tomorrow Planner ---
    st.subheader("📅 Tomorrow Planner")
    if st.button("Show Tomorrow Plan"):
        try:
            res_json = requests.get(f"{BASE_URL}/tomorrow-plan").json()
            plan_text = res_json.get("tomorrow_plan") or res_json.get("plan") or res_json.get("message")
            if plan_text:
                st.info(plan_text)
            elif isinstance(res_json, list) and len(res_json) > 0:
                st.dataframe(pd.DataFrame(res_json), use_container_width=True)
            else:
                st.info("No tasks scheduled or generated for tomorrow yet.")
        except Exception as e:
            st.error(f"Error: {e}")

    # --- Weekly Review ---
    st.subheader("📊 Weekly Review")
    if st.button("Show Weekly Review"):
        try:
            res_json = requests.get(f"{BASE_URL}/weekly-review").json()
            review_text = res_json.get("weekly_review") or res_json.get("review") or res_json.get("summary")
            if review_text:
                st.success(review_text)
            elif isinstance(res_json, list) and len(res_json) > 0:
                st.dataframe(pd.DataFrame(res_json), use_container_width=True)
            else:
                st.info("Weekly review summary is currently empty.")
        except Exception as e:
            st.error(f"Error: {e}")

    # --- End Of Day Summary ---
    st.subheader("🚀 End Of Day Summary")
    if st.button("Run EOD"):
        try:
            response = requests.post(f"{BASE_URL}/run-eod")
            if response.status_code == 200:
                res_data = response.json()
                
                # Show execution success confirmation first
                st.success(
                    res_data.get(
                        "message", 
                        "EOD Summary processed successfully!"
                    )
                )
                
                # Render the actual AI productivity summary block below it
                if res_data.get("summary"):
                    st.markdown("### 📝 AI Summary")
                    st.info(res_data["summary"])
            else:
                st.error(f"Server returned error code {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Error processing EOD Summary: {e}")
    # --- LangGraph Productivity Agent ---
    st.subheader("🤖 LangGraph Productivity Agent")
    if st.button("Run Productivity Agent", key="btn_run_agent"):
        try:
            res_json = requests.get(f"{BASE_URL}/test-agent").json()
            agent_output = None
            
            if isinstance(res_json, dict):
                agent_output = (
                    res_json.get("agent_response")
                    or res_json.get("output")
                    or res_json.get("response")
                )
        
                if not agent_output:
                    if len(res_json) == 1:
                        agent_output = list(res_json.values())[0]
                    else:
                        agent_output = res_json
            else:
                agent_output = res_json

            # Render output safely based on type
            if agent_output:
                if isinstance(agent_output, (dict, list)):
                    st.json(agent_output)
                else:
                    st.info(str(agent_output))
            else:
                st.warning("Agent executed successfully, but returned an empty response format.")
                
        except Exception as e:
            st.error(f"Error executing agent: {e}")


