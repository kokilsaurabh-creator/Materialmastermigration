import subprocess
from pathlib import Path
import io
import os
import math
import xml.sax.saxutils as saxutils
import re  # <--- NEW: Added regex to fix Excel row count validation

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Migration Cockpit", page_icon="🏢", layout="wide")

# --- 2. DATABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception:
    st.error("Database not connected. Please check your secrets.toml file.")

# --- 3. SESSION STATE INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state['step'] = 1 
if 'current_project' not in st.session_state:
    st.session_state['current_project'] = None

def get_git_branch():
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=True,
        )
        branch_name = result.stdout.strip()
        return branch_name or "Detached HEAD"
    except Exception:
        return "No Git Branch"

# --- SCREEN 1: PROJECT SETUP ---
def render_project_setup():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.markdown("## 🏢") 
    with col2:
        st.title("Master Data Migration Cockpit")
    st.markdown("---")

    if 'flash_message' in st.session_state:
        st.toast(st.session_state['flash_message'], icon="✅")
        del st.session_state['flash_message'] 

    try:
        response = supabase.table("migration_projects").select("project_name").execute()
        existing_projects = [row['project_name'] for row in response.data]
    except Exception:
        existing_projects = []

    tab1, tab2 = st.tabs(["📁 Select Existing Project", "➕ Create New Project"])

    with tab1:
        st.subheader("Resume Migration")
        if not existing_projects:
            st.info("No projects found.")
        else:
            selected_project = st.selectbox("Select Project", options=existing_projects)
            if st.button("Open Project Workspace", type="primary"):
                st.session_state['current_project'] = selected_project
                st.session_state['step'] = 2 
                st.rerun()

    with tab2:
        st.subheader("Initialize New Setup")
        new_project_name = st.text_input("Project Name")
        new_master_type = st.selectbox("Master Data Type", ["Material Master", "Vendor Master", "Customer Master"])
        
        if st.button("Create & Configure", type="primary"):
            if new_project_name in existing_projects:
                st.error("Project exists. Choose a different name.")
            elif new_project_name:
                try:
                    supabase.table("migration_projects").insert({
                        "project_name": new_project_name, 
                        "master_type": new_master_type
                    }).execute()
                    
                    st.session_state['current_project'] = new_project_name
                    st.session_state['step'] = 2 
                    st.rerun()
                except Exception as e:
                    st.error(f"DB Error: {e}")

# --- SCREEN 2: CONFIGURATION DASHBOARD ---
def render_configuration_dashboard():
    # Sidebar Navigation
    st.sidebar.caption(f"Branch: {get_git_branch()}")
    st.sidebar.markdown(f"### 📁 {st.session_state.get('current_project') or 'No Project Selected'}")
    st.sidebar.markdown("---")
    
    menu_selection = st.sidebar.radio(
        "Workspace Menu",
        options=[
            "1. Master Data Field Mapping",
            "2. Upload Fixed Rules",
            "3. Upload & Download XML"
        ]
    )
    
    if st.sidebar.button("← Switch Project"):
        st.session_state['step'] = 1
        st.session_state['current_project'] = None
        # Clear generated XML from memory when switching projects
        if 'generated_xml' in st.session_state:
            del st.session_state['generated_xml']
        st.rerun()

    # --- GLOBAL SAP VIEWS DICTIONARY ---
    sap_views = {
        "1. Basic Data (S_MARA)": {
            "Product Number": True, "Product Type": True, "Description": True,
            "Language Key": True, "Base Unit of Measure (ISO Format)": True,
            "Product Group": False, "Change Number": False, "Revision Level": False,
            "GTIN": False, "GTIN Category": False, "Division": False,
            "Old Product Number": False, "Indicator: Batch Management Required": False,
            "Valid From": False, "Competitor": False, "Industry Standard Description": False,
            "Size/Dimensions": False, "Laboratory / Design Office": False,
            "External Product Group": False, "General Item Category Group": False,
            "Authorization Group": False, "Cross-Plant Product Status": False,
            "Valid-From Date": False, "Level of Explicitness for Serial Number": False,
            "Indicator: QM in Procurement Is Active": False, "ANP Code": False,
            "Gross Weight": False, "Net Weight": False, "Unit of Weight (ISO Format)": False,
            "Length": False, "Width": False, "Height": False,
            "Unit for Length/Width/Height (ISO Format)": False, "Volume": False,
            "Volume Unit": False, "Capacity Usage": False, "Compliance Relevant": False,
            "Indicator: Product Is Configurable": False, "Order Unit of Measure (ISO Format)": False,
            "Purchasing Value Key": False, "State of Variable Purchase Order Unit": False,
            "Internal Product Number": False, "Manufacturer Part Number": False,
            "Manufacturer Number": False, "Manufacturer Part Profile": False,
            "Transportation Group": False, "Cross-Distribution Chain Product Status": False,
            "Valid From Date for Status": False, "Billing Cycle": False,
            "Billing Cycle Determination Rule": False, "Assignment Schema": False,
            "Product Group: Packaging Materials": False, "Packaging Product Type": False,
            "Allowed Packaging Weight": False, "Unit of Allowed Packaging Weight": False,
            "Excess Weight Tolerance for HU": False, "Allowed Packaging Volume": False,
            "Unit of Allowed Packaging Volume": False, "Indicator: Product Is Closed Packaging": False,
            "Excess Volume Tolerance for HU": False, "Period Indicator for Shelf Life": False,
            "Storage Conditions": False, "Temperature Conditions Indicator": False,
            "Container Requirements": False, "Hazardous Product Number": False,
            "Label Type": False, "Label Form": False, "Number of Goods Receipt/Issue Slips": False,
            "Indicator: Approved Batch Rec. Required": False, "Total Shelf Life": False,
            "Minimum Remaining Shelf Life": False, "Indicator for the Shelf Life Expiration Date": False,
            "Storage Percentage": False, "Rounding Rule for Calculation of SLED": False,
            "Handling Indicator": False, "Warehouse Product Group": False,
            "Handling Unit Type": False, "Indicator: Quality": False,
            "Indicator: Sales": False, "Indicator: Storage": False,
            "Indicator: Purchasing": False, "Material Code": False
        },
        "2. Additional Descriptions (S_MAKT)": {
            "Product Number": True, "Language Key": True, "Product Description": True
        },
        "3. Alternative Units of Measure (S_MARM)": {
            "Product Number": True, "Alternative Unit of Measure (ISO Format)": True,
            "Denominator for Conversion to Base Unit": True, "Numerator for Conversion to Base Unit": True,
            "GTIN": False, "GTIN Category": False, "Length": False, "Width": False,
            "Height": False, "Unit for Length/Width/Height (ISO Format)": False,
            "Gross Weight": False, "Unit of Weight (ISO Format)": False,
            "Volume": False, "Volume Unit (ISO Format)": False,
            "Lower-Level Unit (ISO Format)": False, "Capacity Usage": False
        },
        "4. Additional GTINs (S_MEAN)": {
            "Product Number": True, "Alternative Unit of Measure (ISO Format)": True,
            "GTIN": False, "GTIN Category": False
        },
        "5. Warehouse Product (S_MATLWH)": {
            "Product Number": True, "Warehouse Number": True, "Party Entitled to Dispose": True,
            "Process Block Profile": False, "Process Type Determination Indicator": False,
            "Cycle Counting Indicator": False, "Required Minimum Shelf Life": False,
            "Preferred UoM": False, "Putaway Control Indicator": False,
            "Storage Section Indicator": False, "Storage Bin Type": False,
            "Bulk Storage Indicator": False, "Stock Removal Control Indicator": False,
            "Stock Determination Group": False, "Staging Area or Door Determination Group": False
        },
        "6. Warehouse Product Storage Type (S_MATLWHST)": {
            "Product Number": True, "Warehouse Number": True, "Party Entitled to Dispose": True,
            "Storage Type": True, "Storage Section Indicator": False, "Storage Bin Type": False,
            "Sort Rule for Empty Storage Bin Search": False, "Maximum Number of Bins": False,
            "Putaway Threshold of Storage Bin": False, "Putaway Sequence": False,
            "Quantity Classification": False, "Putaway Quantity Classification": False,
            "Indicator: Split During Putaway": False, "Indicator: Skip During Putaway": False,
            "Indicator: No Replenishment": False, "Minimum Replenishment Quantity": False,
            "Unit of Measure for Replenishm. Quantity": False, "Minimum Quantity": False,
            "Unit of Measure for Minimum Quantity": False, "Maximum Quantity": False,
            "Unit of Measure for Maximum Quantity": False, "Min.Qty (% of Max. Qty)": False
        },
        "7. Distribution Chains (S_MVKE)": {
            "Product Number": True, "Sales Organization": True, "Distribution Channel": True,
            "Sales Unit (ISO Format)": False, "Delivery Plant": False,
            "Distribution-Chain-Spec. Product Status": False, "Valid-From Date for Product Status": False,
            "Indicator: Cash Discount": False, "Minimum Delivery Quantity": False,
            "Minimum Order Quantity in Base UoM": False, "Delivery Unit": False,
            "Unit of Measure (ISO) of Delivery Unit": False, "Default Contract Term": False,
            "Alternative Contract Term 1 & 2": False, "Unit for Contract Term": False,
            "Default Extension Period": False, "Alternative Extension Period 1 & 2": False,
            "Unit for Extension Period": False, "Rounding Profile": False,
            "Product Pricing Group": False, "Volume Rebate Group": False,
            "Item Category Group": True, "Account Assignment Group": False,
            "Volume Commission Group": False, "Pricing Reference Product": False,
            "Product Statistics Group": False, "Product Group 1 to 5": False
        },
        "8. Tax Classification (S_MLAN)": {
            "Product Number": True, "Country/Region": True, "Tax Category 1": True,
            "Tax Classification 1": True, "Tax Category 2": False,
            "Tax Classification 2": False, "Tax Category 3": False,
            "Tax Classification 3": False, "Tax Category 4": False,
            "Tax Classification 4": False, "Tax Category 5": False,
            "Tax Classification 5": False, "Tax Category 6": False,
            "Tax Classification 6": False, "Tax Category 7": False,
            "Tax Classification 7": False, "Tax Category 8": False,
            "Tax Classification 8": False, "Tax Category 9": False,
            "Tax Classification 9": False,
        },
        "9. Plant Data (S_MARC)": {
            "Product Number": True, "Plant": True, "MRP Type": False,
            "MRP Controller": False, "Availability Check": False,
            "Plant-Specific Product Status": False, "Valid From Date for Status": False,
            "Profit Center": False, "Unit of Issue (ISO Format)": False,
            "Indicator: Batch Management Req.": False, "Serial Number Profile": False,
            "Indicator: Neg. Stocks Allowed in Plant": False, "Stock Determination Group": False,
            "Loading Group": False, "Indicator: Co-Product": False,
            "Batch Entry in Production": False, "Indicator: Critical Part": False,
            "Indicator: Documentation Required": False, "Inspection Interval in Days": False,
            "Quality Management Control Key": False, "Certificate Type": False,
            "Country/Region of Origin": False, "Region of Origin": False,
            "Taxes in International Trade": False, "Material CFOP Category": False,
            "Purchasing Group": False, "Indicator: Post to Inspection Stock": False,
            "Indicator: Source List Required": False, "Indicator: Autom. Purchase Order Allowed": False,
            "Tax Indicator": False, "ABC Indicator": False, "MRP Group": False,
            "Strategy Group": False, "Reorder Point": False, "Planning Time Fence": False,
            "Planning Cycle": False, "Consumption Mode": False,
            "Consumption Period: Backward/Forward": False, "Mixed MRP Indicator": False,
            "Planning Product": False, "Planning Plant": False, "Plng. Conv. Factor": False,
            "Lot Sizing Procedure": False, "Minimum Lot Size": False, "Maximum Lot Size": False,
            "Fixed Lot Size": False, "Storage Cost Indicator": False,
            "Lot Size Independent Cost": False, "Currency for Lot Size Ind. Cost": False,
            "Assembly Scrap (%)": False, "Maximum Stock Level": False, "Rounding Value": False,
            "Takt Time": False, "Rounding Profile": False, "Safety Stock": False,
            "Minimum Safety Stock": False, "Safety Time (in Workdays)": False,
            "Service Level Warehouse": False, "Coverage Profile": False,
            "Safety Time Indicator": False, "Safety Time Period Profile": False,
            "MRP Relevancy for Dependent Requirements": False, "Safety Stock Method": False,
            "Individual / Collective Requirements": False, "Component Scrap in Percent": False,
            "Requirements Group": False, "Discontinuation Ind.": False,
            "Effective-Out Date": False, "Follow-Up Product": False,
            "Indicator: Repetitive Manufa. Allow": False, "Repetitive Manufacturing Profile": False,
            "Procurement Type": False, "Special Procurement Type": False,
            "Issue Storage Location": False, "Replenishment Lead Time": False,
            "Cross-Project": False, "Default Storage Loc. for Ext. Procurement": False,
            "Planning Calendar": False, "In-House Production Time": False,
            "Planned Delivery Time": False, "Goods Receipt Processing Time": False,
            "Backflush": False, "Default Supply Area": False, "JIT Delivery Sched.": False,
            "Indicator: Bulk Material": False, "Scheduling Margin Key": False,
            "Period Type": False, "Fiscal Year Variant": False, "Splitting Indicator": False,
            "Reference Plant for Consumption": False, "Reference Product for Consumption": False,
            "Use Referenced Consumption Data Until": False, "Multiplier for Reference Product": False,
            "Indicator: Reset Forecast Model Auto": False, "Indicator: Correction Factors": False,
            "Base Quantity": False, "Overdelivery Tolerance Limit": False,
            "Underdelivery Tolerance Limit": False, "Indicator: Unlimit. Overdelivery Allowed": False,
            "Production Unit (ISO Format)": False, "Production Supervisor": False,
            "Production Scheduling Profile": False, "Setup and Teardown Time": False,
            "Interoperation Time": False, "Processing Time": False, "Cycle Counting Indicator": False,
            "Indicator: Cycle Counting Fixed": False, "Do Not Cost": False,
            "Variance Key": False, "Costing Lot Size": False, "Maximum Storage Period": False,
            "Unit for Maximum Storage Period": False, "Shipping Setup Time": False,
            "Shipping Processing Time": False, "Base Quantity for Capacity Planning": False,
            "Indicator: Storage": False, "Indicator: Work Scheduling": False,
            "Indicator: Purchasing": False, "Indicator: Quality": False, "Indicator: Sales": False
        },
        "10. Forecasting Data (S_MPOP)": {
            "Product Number": True, "Plant": True, "Forecast Model": False,
            "Hist. Periods": False, "Forecast Periods": False, "Periods Per Season": False,
            "Initialization Periods": False, "Fixed Periods": False, "Initialization": False,
            "Tracking Limit": False, "Model Selection": False, "Selection Procedure": False,
            "Indicator: Param. Optimization": False, "Optimization Level": False,
            "Weighting Group": False, "Alpha Factor": False, "Beta Factor": False,
            "Gamma Factor": False, "Delta Factor": False
        },
        "11. Storage Locations (S_MARD)": {
            "Product Number": True, "Plant": True, "Storage Location": True, "Storage Bin": False
        },
        "12. Production Resources Tools (S_CRFH)": {
            "Product Number": True, "Plant": True, "PRT Usage": False,
            "Grouping Key 1": False, "Grouping Key 2": False, "PRT Control Profile": False,
            "Ind: PRT Control Profile Is Referenced": False, "Standard Text Key": False,
            "Ind: Standard Text Key Is Referenced": False, "Quantity Formula": False,
            "Ind: Quantity Formula Is Referenced": False, "Usage Value Formula": False,
            "Ind: Usage Value Formula Is Referenced": False, "Start Date Reference": False,
            "Ind: Start Refer. of Usage Is Referenced": False, "Offset to Start": False,
            "Offset to Start Unit (ISO Format)": False, "Ind: Offset Start of Usage Is Referenced": False,
            "End Date Reference": False, "Ind: End Refer. of Usage Is Referenced": False,
            "Offset to End": False, "Offset to End Unit (ISO Format)": False,
            "Ind: Offset End of Usage Is Referenced": False
        },
        "13. Inspection Setup Data (S_QMAT)": {
            "Product Number": True, "Plant": True, "Inspection Type": True,
            "Indicator: Preferred Inspection Type": False, "Indicator: Active": False,
            "Indicator: Post to Inspection Stock": False, "Indicator: Serial Numbers Possible": False,
            "Dynamic Modification Rule": False, "Indicator: Skips Allowed": False,
            "Inspection Lot Summary": False, "Control Lot Creation": False,
            "Indicator: Inspection with Task List": False, "Indicator: Inspect by Batch": False,
            "Ind: Automatic Specification Assignment": False, "Indicator: Inspect Characteristics": False,
            "Sampling Procedure": False, "Indicator: 100% Inspection": False,
            "Inspection Percentage": False, "Indicator: Manual Sample Calculation": False,
            "Indicator: Manual Sample Entry": False, "Average Inspection Days": False,
            "Indicator: Automatic Usage Decision": False, "Quality Score Procedure": False
        },
        "14. MRP Area (S_MRP_AREA)": {
            "Product Number": True, "MRP Area": True, "Plant": True, "MRP Type": False
        }
    }

    # --- MAIN WORKSPACE: FIELD MAPPING ---
    if menu_selection == "1. Master Data Field Mapping":
        st.header("Master Data Field Mapping")
        st.markdown("Configure migration rules. **Note: Fields marked with 🔴 are mandatory in SAP.**")
        
        with st.expander("📊 View All Saved Mappings for this Project"):
            try:
                res_all = supabase.table("field_mappings").select("view_name, field_name, is_mandatory, mapping_type, fixed_value").eq("project_name", st.session_state['current_project']).execute()
                
                if res_all.data:
                    df_mappings = pd.DataFrame(res_all.data)
                    df_mappings.columns = ["SAP View", "Field Name", "Is Mandatory?", "Mapping Rule", "Fixed Value"]
                    st.dataframe(df_mappings, use_container_width=True, hide_index=True)
                else:
                    st.info("No fields have been mapped for this project yet.")
            except Exception as e:
                st.error(f"Could not load mappings: {e}")

        mapping_options = [
            "Blank (Default)", 
            "Keep Blank", 
            "Fixed Values", 
            "Based on Fixed Rules", 
            "Based on User Input"
        ]

        configurations_to_save = []
        validation_error = False

        st.markdown("---")
        
        selected_view_header = st.selectbox(
            "Select SAP View to Configure", 
            options=list(sap_views.keys()),
            index=0
        )
        
        fields_to_render = sap_views[selected_view_header]
        view_name = selected_view_header.split(" (")[0]
        sap_struct = selected_view_header.split("(")[1].replace(")", "")
        
        try:
            response = supabase.table("field_mappings").select("*").eq(
                "project_name", st.session_state['current_project']
            ).eq("view_name", view_name).execute()
            
            existing_mappings = {row['field_name']: row for row in response.data}
        except Exception as e:
            st.error(f"Error loading existing data: {e}")
            existing_mappings = {}

        st.markdown(f"#### Configuring: {selected_view_header}")
        
        h1, h2, h3 = st.columns([2, 2, 2])
        h1.markdown("**SAP Field**")
        h2.markdown("**Mapping Strategy**")
        h3.markdown("**Fixed Value Input**")
        st.markdown("---")

        for field, is_mand in fields_to_render.items():
            saved_data = existing_mappings.get(field, {})
            saved_mapping = saved_data.get('mapping_type', 'Blank (Default)')
            saved_value = saved_data.get('fixed_value', "")
            if saved_value is None: 
                saved_value = ""
                
            try:
                mapping_index = mapping_options.index(saved_mapping)
            except ValueError:
                mapping_index = 0

            c1, c2, c3 = st.columns([2, 2, 2])
            
            with c1:
                if is_mand:
                    st.markdown(f"🔴 **{field}**")
                else:
                    st.markdown(f"⚪ {field}")
            
            with c2:
                selection = st.selectbox(
                    "Rule", 
                    options=mapping_options, 
                    index=mapping_index, 
                    key=f"map_{sap_struct}_{field}",
                    label_visibility="collapsed"
                )
                
                if is_mand and selection == "Blank (Default)":
                    st.error("Mandatory. Map this field or select 'Keep Blank'.")
                    validation_error = True
            
            with c3:
                fixed_val = None
                if selection == "Fixed Values":
                    fixed_val = st.text_input(
                        "Value", 
                        value=saved_value, 
                        placeholder="Enter value...", 
                        key=f"val_{sap_struct}_{field}",
                        label_visibility="collapsed"
                    )
                    if not fixed_val:
                        st.warning("Value required")
                        validation_error = True
            
            configurations_to_save.append({
                "project_name": st.session_state['current_project'],
                "sap_structure": sap_struct,
                "view_name": view_name,
                "field_name": field,
                "is_mandatory": is_mand,
                "mapping_type": selection,
                "fixed_value": fixed_val
            })

        st.markdown("---")
        
        if st.button(f"💾 Save {view_name} Configurations", type="primary"):
            if validation_error:
                st.error("Cannot save. Please resolve the errors highlighted above.")
            else:
                try:
                    supabase.table("field_mappings").upsert(
                        configurations_to_save, 
                        on_conflict="project_name,sap_structure,field_name"
                    ).execute()
                    st.success(f"{view_name} configurations saved successfully!")
                except Exception as e:
                    st.error(f"Database error during save: {e}")

    # --- UPLOAD FIXED RULES MODULE ---
    elif menu_selection == "2. Upload Fixed Rules":
        st.header("Upload Fixed Rules")
        st.markdown("Download the dynamic template, fill in your mapping logic, and upload the completed file.")
        
        current_proj = st.session_state['current_project']
        
        with st.expander("📊 View Currently Saved Rules in Database"):
            try:
                res_rules = supabase.table("project_fixed_rules").select("rule_data").eq("project_name", current_proj).execute()
                if res_rules.data:
                    saved_rules_df = pd.DataFrame([row['rule_data'] for row in res_rules.data])
                    st.dataframe(saved_rules_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No fixed rules have been uploaded and saved for this project yet.")
            except Exception as e:
                st.error(f"Could not load saved rules: {e}")

        try:
            response = supabase.table("field_mappings").select("field_name").eq("project_name", current_proj).eq("mapping_type", "Based on Fixed Rules").execute()
            rule_fields = [row['field_name'] for row in response.data]
        except Exception as e:
            st.error(f"Error fetching rule fields: {e}")
            rule_fields = []
            
        if not rule_fields:
            st.warning("⚠️ No fields have been mapped to 'Based on Fixed Rules' for this project yet. Go back to Master Data Field Mapping to configure rules.")
        else:
            standard_keys = [
                "Product Type", 
                "Product Group", 
                "Plant", 
                "Sales Organisation", 
                "Distribution Channel"
            ]
            template_columns = standard_keys + rule_fields
            
            st.success(f"Found {len(rule_fields)} fields requiring fixed rules.")
            
            df_template = pd.DataFrame(columns=template_columns)
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False, sheet_name='Fixed Rules')
                worksheet = writer.sheets['Fixed Rules']
                for i, col in enumerate(template_columns):
                    worksheet.set_column(i, i, max(len(col) + 2, 15))
            
            st.download_button(
                label="📥 Download Excel Template",
                data=buffer.getvalue(),
                file_name=f"{current_proj}_Fixed_Rules_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
            
            st.markdown("---")
            
            st.subheader("Upload Completed Rules")
            uploaded_file = st.file_uploader("Upload your filled Excel file", type=["xlsx", "xls"])
            
            if uploaded_file is not None:
                df_uploaded = pd.read_excel(uploaded_file)
                
                st.write("### Data Preview (Pre-Save)")
                st.dataframe(df_uploaded, use_container_width=True)
                
                if st.button("💾 Overwrite & Save Rules", type="primary"):
                    try:
                        supabase.table("project_fixed_rules").delete().eq("project_name", current_proj).execute()
                        records = df_uploaded.to_dict(orient='records')
                        insert_payload = [{"project_name": current_proj, "rule_data": record} for record in records]
                        
                        if insert_payload:
                            supabase.table("project_fixed_rules").insert(insert_payload).execute()
                            st.success("Fixed rules successfully overwritten and saved to the database! Click the expander at the top to view them.")
                        else:
                            st.warning("The uploaded file was empty. Previous rules were deleted.")
                            
                    except Exception as e:
                        st.error(f"Error saving rules: {e}")

    # --- UPLOAD & DOWNLOAD XML MODULE ---
    elif menu_selection == "3. Upload & Download XML":
        st.header("Upload User File & Generate XML")
        st.markdown("Download the final data template, upload your material data, and inject it into the SAP Migration template.")
        
        current_proj = st.session_state['current_project']
        
        base_columns = [
            "Product Number", "Product Description", "Product Type", 
            "Product Group", "Plant", "Sales Organisation", "Distribution Channel"
        ]
        
        try:
            res_mappings = supabase.table("field_mappings").select("*").eq("project_name", current_proj).execute()
            all_mappings = res_mappings.data
            
            user_mapped_fields = [row['field_name'] for row in all_mappings if row['mapping_type'] == "Based on User Input" and row['field_name'] not in base_columns]
            
            res_rules = supabase.table("project_fixed_rules").select("rule_data").eq("project_name", current_proj).execute()
            saved_rules = [row['rule_data'] for row in res_rules.data]
        except Exception as e:
            st.error(f"Error fetching configurations: {e}")
            all_mappings = []
            user_mapped_fields = []
            saved_rules = []
            
        template_columns = base_columns + user_mapped_fields
        
        st.subheader("1. Download Data Template")
        df_user_template = pd.DataFrame(columns=template_columns)
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_user_template.to_excel(writer, index=False, sheet_name='User Data')
            worksheet = writer.sheets['User Data']
            for i, col in enumerate(template_columns):
                worksheet.set_column(i, i, max(len(col) + 2, 15))
        
        st.download_button(
            label="📥 Download User Input Template",
            data=buffer.getvalue(),
            file_name=f"{current_proj}_User_Input_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
        st.markdown("---")
        
        st.subheader("2. Upload Completed Data")
        uploaded_file = st.file_uploader("Upload your filled User Data Excel file", type=["xlsx", "xls"], key="user_data_upload")
        
        if uploaded_file is not None:
            df_uploaded = pd.read_excel(uploaded_file)
            st.write(f"### Data Preview ({len(df_uploaded)} Materials Found)")
            st.dataframe(df_uploaded, use_container_width=True)
            
            if st.button("⚙️ Process Data & Generate XML", type="primary"):
                
                template_path = os.path.join("templates", "Source data for Product.xml")
                
                if not os.path.exists(template_path):
                    st.error("⚠️ Template file not found! Please create a 'templates' folder and place 'Source data for Product.xml' inside it.")
                else:
                    with st.spinner("Assembling Master Data and injecting into XML..."):
                        
                        # 1. Data Assembly Engine
                        final_sap_data = {}
                        user_materials = df_uploaded.to_dict(orient='records')
                        
                        for mat_index, material in enumerate(user_materials):
                            matched_rule = {}
                            for rule in saved_rules:
                                if (str(rule.get("Product Type", "")) == str(material.get("Product Type", "")) and
                                    str(rule.get("Product Group", "")) == str(material.get("Product Group", "")) and
                                    str(rule.get("Plant", "")) == str(material.get("Plant", "")) and
                                    str(rule.get("Sales Organisation", "")) == str(material.get("Sales Organisation", "")) and
                                    str(rule.get("Distribution Channel", "")) == str(material.get("Distribution Channel", ""))):
                                    matched_rule = rule
                                    break
                            
                            for map_config in all_mappings:
                                view_name = map_config['view_name'] 
                                field_name = map_config['field_name']
                                mapping_type = map_config['mapping_type']
                                
                                if view_name not in final_sap_data:
                                    final_sap_data[view_name] = []
                                    
                                while len(final_sap_data[view_name]) <= mat_index:
                                    final_sap_data[view_name].append({})
                                
                                resolved_value = ""
                                if field_name in base_columns or mapping_type == "Based on User Input":
                                    resolved_value = material.get(field_name, "")
                                elif mapping_type == "Fixed Values":
                                    resolved_value = map_config.get('fixed_value', "")
                                elif mapping_type == "Based on Fixed Rules":
                                    resolved_value = matched_rule.get(field_name, "")
                                elif mapping_type in ["Blank (Default)", "Keep Blank"]:
                                    resolved_value = ""
                                    
                                if pd.isna(resolved_value) or resolved_value is None:
                                    resolved_value = ""
                                    
                                final_sap_data[view_name][mat_index][field_name] = resolved_value
                        
                        # 2. XML String Injection Engine
                        with open(template_path, "r", encoding="utf-8") as f:
                            xml_content = f.read()
                            
                        for view_key, rows_list in final_sap_data.items():
                            sheet_name = view_key.split(". ", 1)[-1]
                            sheet_start_tag = f'<Worksheet ss:Name="{sheet_name}"'
                            
                            if sheet_start_tag in xml_content:
                                
                                # Filter only rows where Product Number is not blank
                                valid_rows = [r for r in rows_list if str(r.get("Product Number", "")).strip()]
                                num_new_rows = len(valid_rows)
                                
                                if num_new_rows == 0:
                                    continue
                                
                                full_view_key = [k for k in sap_views.keys() if k.startswith(view_key)][0]
                                exact_column_order = sap_views[full_view_key].keys()
                                
                                sheet_xml_rows = ""
                                for row_dict in valid_rows:
                                    sheet_xml_rows += "    <Row>\n"
                                    for field in exact_column_order:
                                        val = row_dict.get(field, "")
                                        safe_val = saxutils.escape(str(val))
                                        sheet_xml_rows += f'        <Cell><Data ss:Type="String">{safe_val}</Data></Cell>\n'
                                    sheet_xml_rows += "    </Row>\n"
                                
                                parts = xml_content.split(sheet_start_tag, 1)
                                before_sheet = parts[0]
                                sheet_and_after = parts[1]
                                
                                table_parts = sheet_and_after.split("</Table>", 1)
                                inside_table = table_parts[0]
                                after_table = table_parts[1]
                                
                                # --- FIX: Regex to dynamically update the ExpandedRowCount ---
                                def update_row_count(match):
                                    old_count = int(match.group(1))
                                    new_count = old_count + num_new_rows
                                    return f'ss:ExpandedRowCount="{new_count}"'
                                
                                inside_table = re.sub(r'ss:ExpandedRowCount="(\d+)"', update_row_count, inside_table, count=1)
                                # -------------------------------------------------------------
                                
                                xml_content = before_sheet + sheet_start_tag + inside_table + sheet_xml_rows + "</Table>" + after_table
                                
                        st.session_state['generated_xml'] = xml_content
                        st.success("✅ XML successfully generated and ready for SAP Migration Cockpit!")

        if 'generated_xml' in st.session_state:
            st.download_button(
                label="📥 Download Ready-to-Upload SAP XML",
                data=st.session_state['generated_xml'],
                file_name=f"{current_proj}_Migration_Cockpit_Data.xml",
                mime="application/xml",
                type="primary"
            )

def main():
    if st.session_state.get('step') == 1:
        render_project_setup()
    else:
        render_configuration_dashboard()

if __name__ == "__main__":
    main()