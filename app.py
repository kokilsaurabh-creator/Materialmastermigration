import streamlit as st
from supabase import create_client, Client

# 1. Page Configuration
st.set_page_config(page_title="Master Data Migration Cockpit", page_icon="🏢", layout="centered")

# 2. Initialize Supabase Connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

def main():
    # Show any pending toast after a rerun so it remains visible
    pending_toast = st.session_state.pop("pending_toast", None)
    pending_toast_icon = st.session_state.pop("pending_toast_icon", "ℹ️")
    if pending_toast:
        st.toast(pending_toast, icon=pending_toast_icon)

    # Header
    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown("## 🏢") 
    with col2:
        st.title("Master Data Migration Cockpit")
    
    st.markdown("---")

    # Fetch existing projects from Supabase to populate the dropdown
    try:
        response = supabase.table("migration_projects").select("project_name").execute()
        # Extract just the names into a list
        existing_projects = [row['project_name'] for row in response.data]
    except Exception as e:
        st.error(f"Database connection error: {e}")
        existing_projects = []

    tab1, tab2 = st.tabs(["📁 Select Existing Project", "➕ Create New Project"])

    # --- TAB 1: EXISTING PROJECT ---
    with tab1:
        st.subheader("Resume Migration")
        
        if not existing_projects:
            st.info("No projects found. Please create a new project in the next tab.")
        else:
            selected_project = st.selectbox("Select Project", options=existing_projects, key="exist_proj")
            
            if st.button("Open Project Workspace", type="primary"):
                st.session_state['current_project'] = selected_project
                st.session_state['step'] = 2
                st.toast(f"Loading workspace for {selected_project}...", icon="📁")

    # --- TAB 2: NEW PROJECT ---
    with tab2:
        st.subheader("Initialize New Setup")
        
        new_project_name = st.text_input("Project Name", placeholder="e.g., Project Landmark - Phase 1")
        new_master_type = st.selectbox("Master Data Type", options=["Material Master", "Vendor Master", "Customer Master"], key="new_master")
        
        if st.button("Create & Configure", type="primary"):
            if new_project_name.strip() == "":
                st.error("Project Name is required.")
            elif new_project_name in existing_projects:
                st.error("A project with this name already exists. Please choose a different name.")
            else:
                # Insert the new project into Supabase
                insert_data = {
                    "project_name": new_project_name,
                    "master_type": new_master_type
                }
                try:
                    supabase.table("migration_projects").insert(insert_data).execute()
                    st.session_state['current_project'] = new_project_name
                    st.session_state['master_type'] = new_master_type
                    st.session_state['pending_toast'] = f"Project '{new_project_name}' successfully created!"
                    st.session_state['pending_toast_icon'] = "✅"
                    # Force a rerun so the new project appears in Tab 1 instantly
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving to database. Ensure your table exists. Details: {e}")

if __name__ == "__main__":
    main()

