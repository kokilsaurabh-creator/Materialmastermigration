import subprocess
from pathlib import Path
import io
import os
import xml.sax.saxutils as saxutils
import re

import pandas as pd
import streamlit as st
from supabase import create_client, Client
from streamlit_option_menu import option_menu

# --- EXPOUND BASE64 LOGO ---
EXPOUND_LOGO = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wgARCADIAMgDASIAAhEBAxEB/8QAHAABAAIDAQEBAAAAAAAAAAAAAAYHAwQFAggB/8QAGQEBAAMBAQAAAAAAAAAAAAAAAAECAwQF/9oADAMBAAIQAxAAAAH6pAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARGTXpsClwAAAAAAAAAHzl6ivseVWE7vfgdXNcUep60PL9HzNYhCIm1dOvJISvLBOWm3NKLwOFq5ot5Nixqys3LQMNwAAPmm0u9THTz3DF83A5t4vdXDseVfSrr/l6U/Kt3Y0pgz5P3O8f6G/lmPXGkW9W0Yk5EhWwAACNyQfPtg2CAANHH0hqeN4aet1Rq7QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAf//EACoQAAIDAQABAQUJAQAAAAAAAAQFAgMGAQAwEBMUFRYREiAkJjE2QHCA/9oACAEBAAEFAv8AZyNanGuoIrKq/rbbcfEezLaq/OEgnUMhdcwvV56Cl9OAp1Bvnz9dywTUqji2b5em8EchHiVGU3CfOQvchahWxLZaJcnszjLrB96G82M5W4bMVvzDHmfRmbPFD3BYwDQqCt9/Egsvymem7MJu8HX/AEtvaaY5zLc989cVQH0qbv6GiNWWj1tUKiMfyFxmbrhVp/QLwP53HAArB2LSCq5ho2HRLmBRXnE0D8/9FCeL1Q6zzVoxgllGRCqJZZwVkSsQiKo1YsCrtGYDGrYK6WUj8uIaauzgaor0HSSttTVcUjOq20PuudNJpRnc58P7e/tEmwWVbf3sLSSYldZSnGR/2eWMecmKR2/1HKWttTZnWFdiDNfBd/BIKqfOgxnTAaMJVB108qFrp8itogMOPEaP/AH/xAAoEQABBAECAgsAAAAAAAAAAAABAAIDERITITFBEBQgIjBQUWBhobH/2gAIAQMBAT8B83DmnYHxJpjI7RiXV3R96N1kISl8JcRRpZGIZV92tR9E7bLVdWXJGUgCvRaj8sOahvHf5/eyyCOM5NG/QRYooRtbwC0W3dLBt5UtJg5Isa7iEGhuw9o//8QAKBEAAQMDAgMJAAAAAAAAAAAAAQACAxESIQQTMUFREBQgMFBgobHR/9oACAECAQE/AfVyxzckeZp9O2Ju/Mu8skoyVtAUYmxztaDUVVomdbX4ohEyoGc4Wy2tnNNhaSa9f1bbLdzkp6X46D68MmpkkFrjjsBINQnSPdglb77barcfS2uEZZDxKD3N4FOcXZPtH//EAD8QAAIBAwEEBgQKCgMAAAAAAAECAwAEERITITFhBRRBQlFxIzAyUgYQFSIzNGKBkcEWICRAcHJ0gIKxlKGy/9oACAEBAAY/Av4z7KS/iD8N2+llhkWWNuDIcg/u79H9HP6LhLOve5Dl8XbJaOfSRfmOdJcW8gkifgRV1c2z7OZNOlsZ7wFK36QjeM/UkqTYSrLs20NpPA0E67CGLMntdo4iurQXqPNwA3jPke2l65crCW4LxP4CnuYLlJIUGXYd3zoXKSBoCuvXyq3m6wgin3RseDV1a3vEkm93BGfLxpY7u6WJ24Lgk/8AVdOabgz2y7ExfOyoyp4epl6Ls20ovzZpB3vs1JJc56rBjKjvHwr5ONquobmEUAIXzo3vRsGidd5iiG5xyFZWzbqbn0kcrBfvHOr7/D/2tQTfKnSb6Sr6HucqeRGOFXJ6GaQTvDm+WEZCr7381dErZBXszdR4PjxznnTvgLNEybAjiGyOFdNS3QHX1dV38VTG7FXy2o07Xo2RrhV4duD51F/SH/Rr4JwyrrjafDKe3jXQDIoUrfxoMdg8K6anlwb7rjI2eITujyr4RrGoRdUO5fI+pnkvOlbe3DuWx7TYzU8FndNdHVqcsMUcWMjlt+0Rdx++i6WbWqE42rb69JPI/ItUdhd6tLIuvScHdvr63f8/JNTbBMGZzI7E5JNRRW8REc9+jugO7fnOPCopnkubnZHMUdxMXRPIUtyWmtroDG3tn0NipdkrSPL9JLM2p38zWnXctbZ1dUaY7L8KtY02ui2l20QL50nw8qtjNq/Z5RMmk94UbsSXFpcMMNJbSaC3nRuLYPGzJocayQ/M8/U+5Ovsv8AlRx6OVdxU8DXpbZg32Wrq8cOzQnfk5Jpbm6X0vFEPd+Pwq8kmuHkjgYKFIUZyo5eJo6UV5dYQBHypzzqJViDMY2JTXu4jtxURhg2m0i229sYFGVQ7LsBLo5UVjTaHKqu/cWIz/rfUgdNnJG2lhnPP1nuTL7L1o6szc14UJ7rDTd1exf1ZwR9Mctv5Y/KtDvI+/UGLbwaVsszqpXUxpAo9iPZDypdI9lBH91CBQVUHUCDvBohckscszHJJ/sB/8QAKxABAAEDAwMDAgcBAAAAAAAAAREAITFBUWFxgZEwobHR4RAgQHCAwfDx/9oACAEBAAE/If3nRkLIaR5QQoqBSZ3B+mWCXFYE3Md7+516ZqM7sP8Al8qAc0/CdnitK85hLrImFqEBBD71Bo9b9HkpUwNEmO9xJ5qfCNiD2QjsajA1MC5vAsU85yOASwyW3qHMQcc6jYxwyf4c1m2cYDuSOyit9Nkt0DBy0yO0VlkcZS/ot6dLXWo433x1mWXkifEtrX7UYsNKG93aatDTd6dHUmbc0fDF4pFk7L0pr22rxHDqHCniGP2CM7RnnXqSVThLP+2mlu9DxjXbPjijcVufggeOKJBD/lEs7PPNBLJGeomejANDTGeUxK3HFihMlLhog8vHFG9rxQSu+8+isWLiVSSRi9P+AzfEEEYtWQdgRejXrQhiXiOkhTET+ojxVgtQgFAJ6hQBARSHOdKedVvbSlonsTAQaOlXSTQHSTbmav8AQUvsUzR9kOOtPis+HCBZnr701EunCcvZV3ZbxsTxUqYmy01PdBKY3Od+X0ZlYX3nFMwdups7lPO6IkfNWGGVYGDijvT6iPPx+IlAy3NKuUdi0koKSykD4J07DNtKDbP4lIXJrtrUupovYthvet0pgiTdxMxzU7SatURnSAS5rDIBgwBHUhPUjzAsfs8U/wAjZhXehNBuN+Xl/KwNAusgCbYVjlNjbCOlM8oJCiiz4KSQASvH6Uoksks24qUXdO0R9ulqWTbEClegeP4A/wD/2gAMAwEAAgADAAAAEPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPOPfPPPPPPPPPPCq62/wAzMV/zzzx49z5wHZ5zzzzzxzzxzzxzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz/8QAJhEBAAIABQIGAwAAAAAAAAAAAQARITFBUYFhkSAwUGBxscHh8P/aAAgBAwEBPxD1dVEp18zX44L9/uFo2ZD+xieAW5pmRsSrZS4t79PiJZIB1xsuhvs67REVLKVrqb9yuY8AtDyofmbDizpqqvK8+esS3r+zw85CVUBgsY1ZDAWxpplUDqFwyBlxiQqmj2j/AP/EACYRAQABAwMDAwUAAAAAAAAAAAERACExQVFhcYHBIDBQYJGx0fD/2gAIAQIBAT8Q+XIFA7nuaDi4fh67FM0cNcP660JRhs2ks/16IgJ0QA6wfbm2tLyzdFoYlI5uTbehXJgDNowOI5szfahBMCOwLxW/WYkmZjMY7cUBYt4Hp7HCClXNAkhKFlJSgC1lnM0pMuFZRqOmI80nLLz9I//EACYQAQEAAgICAAYCAwAAAAAAAAERACExQVFhMHGBkaGxECBAcID/2gAIAQEAAT8Q/wBzLDOl3NlkWB3XWQwSq3kRH/GBkAFV6x0yHKHQD6B9Dt/CwTXhdbdAfQEekuYn/wBw5B0rYmAt3r2+EUWzvzncSwZSzLSR0DHX2UwRVejnC0PYSxLcHW9PgBTeBrjtZnq0jcVLJpxaXtKxRB4WAYYty4jYFeNkF4xZM6SAKxTQCLBrHSTpihWPAF3dC9YYB24JggIjwGnesHf0KUyqSIJs3s+C6BUl3acHh8oeA4EAVOO242ATG+GrTjkSaQg5VEWFve9ZYxmtGCg1JoKFFmRWeMTjUgeNBHpAQIjqmQ5ZYVHtAka2KZQhzhcAgqYGwuirifVMgzVdmC8IkJANqxpcIbPEdV0hVuoXUg9AvaV1mpvcSIBaEzeZXZX6NFrRAcLl/wAk75BkTswDC13Gm4RoNaMiaDoihDs0JxZ8MHRFCaaBqqT7X4IB2/oIKlCcXnvNWufpcadvbzzhtG21jdoxwxfpgunAoOyBbiWJ9Zm31wbT4Kn4wPzFozkMgn0OBgQgEA+2NCD3HO0oqBdHtVhLxpABY51EvgAAvkEm1fKJXA7Miof9k+A+ZZqzONT+JEnMIugHrG5qy7dGRdxI93J4p2SkbM1SuVbVwNVq91XjbtswXTBcwAkR0BSLC2GHwulwQYZdr6t/BnFlp5/avucnYtgNIq9w7NInpHJwU2YvQBPziHfi7qgAG08rMBOUAqeJ/iftx/CMKCEr7F1gKNQGwpHBRAAt3QMmNF0pKAuqOA0pIHuA6mmkB33gUSiCA2RW0VAQl5Q3gQijjRQKjetGAF3kB6uGIcMOIdEBcB7XG7IZRWweRCfE3dpPh+9/jk7GsBp7JtoHzmbivMe4ePk6Oq7P6aOHuKyA1AonCXnEjMbuohTScSNba31XNJ7ot+UEytKAWHQfLpvAMEGw6TeX3h8HmQ21aIadR01iyjtohQ9ACAAA/wCAf//Z"

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Migration Studio", page_icon="🏢", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PROFILES ---
LOGIN_THEME_CSS = """
    <style>
        /* Base SaaS Background */
        .stApp {
            background-color: #f4f7f9;
            color: #0f172a;
        }
        
        /* Elevate the main workspace into a centered, perfectly sized white card */
        .block-container {
            background-color: #ffffff !important;
            max-width: 480px !important;
            margin-top: 10vh !important;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            padding: 3rem 3rem !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
        }

        /* Input Labels */
        .input-label {
            font-size: 0.75rem; 
            font-weight: 700; 
            color: #64748b; 
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px; 
            display: block;
        }

        /* Streamlit Input Overrides */
        div[data-baseweb="select"] > div {
            background-color: #f8fafc !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
            color: #0f172a !important;
        }
        div[data-baseweb="select"] > div:focus-within {
            border-color: #0a6ed1 !important;
        }
        div[data-baseweb="select"] span {
            color: #0f172a !important;
            font-size: 0.95rem !important;
        }
        
        .stTextInput > div > div > input {
            background-color: #f8fafc !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
            color: #0f172a !important;
            padding: 10px 14px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #0a6ed1 !important;
            box-shadow: 0 0 0 1px #0a6ed1 !important;
        }

        /* Primary Button */
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #0a6ed1 !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            min-height: 44px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            margin-top: 1rem !important;
            box-shadow: 0 4px 6px rgba(10, 110, 209, 0.2) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #0854a0 !important;
            box-shadow: 0 6px 12px rgba(10, 110, 209, 0.3) !important;
            transform: translateY(-1px) !important;
        }
        
        /* Hide Default Elements */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
    </style>
"""

LIGHT_THEME_CSS = """
    <style>
        /* Base SaaS Background */
        .stApp {
            background-color: #f8fafc;
            color: #0f172a;
        }
        
        /* Elevate the main workspace into a crisp, centered white card */
        .block-container {
            padding: 2rem 3rem !important;
            max-width: 1440px !important;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            margin-top: 2rem !important;
            margin-bottom: 2rem !important;
            border: 1px solid #e2e8f0;
        }

        /* --- GLOBAL BUTTON STYLING --- */
        div[data-testid="stButton"] > button {
            background-color: #ffffff;
            color: #0056b3;
            border: 1px solid #0056b3;
            border-radius: 6px;
            padding: 4px 16px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #f0f7ff;
            color: #004494;
        }
        
        /* Primary Button Override */
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #0056b3;
            color: white;
            border: none;
            min-height: 44px;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #004494;
        }

        /* --- HEADER & BRANDING CSS --- */
        .brand-title {
            font-size: 1.45rem;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }
        .brand-subtitle {
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            color: #64748b;
            text-transform: uppercase;
            margin: 0;
        }
        
        /* --- METADATA & KPI CSS --- */
        .meta-label {
            font-size: 0.7rem;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin: 0 0 4px 0;
        }
        .meta-value {
            font-size: 0.95rem;
            font-weight: 600;
            color: #334155;
        }
        
        /* Status Pill */
        .status-pill {
            background-color: #ecfdf5;
            border: 1px solid #a7f3d0;
            color: #065f46;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        .status-dot {
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
        }

        /* --- PROJECT DISPLAY CSS --- */
        .project-title {
            font-size: 1.5rem;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }

        /* Change Project Utility Button */
        div[data-testid="column"]:nth-of-type(4) div[data-testid="stButton"] > button {
            background-color: transparent;
            border: 1px solid #e2e8f0;
            color: #64748b;
            min-height: 34px;
            padding: 2px 12px;
            font-size: 0.8rem;
            margin-top: 18px;
        }
        div[data-testid="column"]:nth-of-type(4) div[data-testid="stButton"] > button:hover {
            background-color: #f8fafc;
            color: #0f172a;
            border-color: #cbd5e1;
        }

        /* Main Workspace Typography */
        h1, h2, h3, h4 {
            color: #0f172a;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 600;
        }
        
        /* Premium Input Fields */
        .stSelectbox > div > div, .stTextInput > div > div > input {
            border-radius: 6px !important;
            border: 1px solid #cbd5e1 !important;
            background-color: #ffffff;
        }
        .stTextInput > div > div > input:focus, .stSelectbox > div > div:focus {
            border-color: #0056b3 !important;
            box-shadow: 0 0 0 1px #0056b3 !important;
        }

        /* Hide Streamlit default UI elements */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
    </style>
"""

# --- 2. DATABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception:
    st.error("⚠️ Database not connected. Please check your secrets.toml file.")

# --- 3. SESSION STATE INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state['step'] = 1 
if 'current_project' not in st.session_state:
    st.session_state['current_project'] = None
if 'selected_master' not in st.session_state:
    st.session_state['selected_master'] = "Material Master"
if 'selected_nav' not in st.session_state:
    st.session_state['selected_nav'] = "Field Mapping"

@st.cache_data(show_spinner=False)
def get_all_saved_mappings(project_name: str):
    try:
        res_all = supabase.table("field_mappings").select(
            "view_name, field_name, is_mandatory, mapping_type, fixed_value"
        ).eq("project_name", project_name).execute()
        return res_all.data
    except Exception:
        return []

@st.cache_data(show_spinner=False)
def get_view_saved_mappings(project_name: str, view_name: str):
    try:
        response = supabase.table("field_mappings").select("*").eq(
            "project_name", project_name
        ).eq("view_name", view_name).execute()
        return {row['field_name']: row for row in response.data}
    except Exception:
        return {}

# --- SCREEN 1: PROJECT SETUP (CLEAN LIGHT MODE) ---
def render_project_setup():
    st.markdown(LOGIN_THEME_CSS, unsafe_allow_html=True)
    
    # Logo and Titles (Width auto implemented to prevent stretching)
    st.markdown(f"""
        <div style="position: relative; display: flex; justify-content: center; margin-bottom: 1.5rem;">
            <img src="{EXPOUND_LOGO}" style="height: 70px; width: auto; object-fit: contain; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.05));" alt="Expound Logo"/>
        </div>
        <h1 style="text-align: center; color: #0f172a; font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.02em;">Expound Master Data Hub</h1>
        <p style="text-align: center; color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2rem;">S/4HANA Migration Engine <span style="color: #cbd5e1; padding: 0 4px;">|</span> Enterprise-Grade Precision</p>
    """, unsafe_allow_html=True)

    if 'flash_message' in st.session_state:
        st.toast(st.session_state['flash_message'], icon="✅")
        del st.session_state['flash_message'] 

    try:
        response = supabase.table("migration_projects").select("project_name").execute()
        existing_projects = [row['project_name'] for row in response.data]
    except Exception:
        existing_projects = []

    # Segmented Control for Login Mode
    mode = option_menu(
        menu_title=None,
        options=["Open Existing Project", "Create New Migration"],
        icons=["folder2-open", "plus-circle"],
        orientation="horizontal",
        default_index=0,
        styles={
            "container": {
                "max-width": "100%", "margin": "0 auto 2rem auto",
                "background-color": "#f1f5f9", "padding": "4px",
                "border-radius": "8px", "border": "1px solid #e2e8f0"
            },
            "icon": {"font-size": "13px", "color": "inherit"},
            "nav-link": {
                "font-size": "13px", "text-align": "center", "margin": "0",
                "padding": "10px", "border-radius": "6px", "color": "#64748b",
                "transition": "all 0.2s ease"
            },
            "nav-link-selected": {
                "background-color": "#ffffff", "color": "#0a6ed1",
                "font-weight": "600", "box-shadow": "0 1px 3px rgba(0,0,0,0.1)"
            }
        }
    )

    if mode == "Open Existing Project":
        if not existing_projects:
            st.info("No projects found. Please create one.")
        else:
            st.markdown("<label class='input-label'>Select Project Space</label>", unsafe_allow_html=True)
            selected_project = st.selectbox("Select Project Space", options=existing_projects, label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Launch Workspace ➔", type="primary", use_container_width=True):
                st.session_state['current_project'] = selected_project
                try:
                    project_row = supabase.table("migration_projects").select("master_type").eq("project_name", selected_project).single().execute()
                    if project_row.data and project_row.data.get('master_type'):
                        st.session_state['selected_master'] = project_row.data['master_type']
                except Exception:
                    st.session_state['selected_master'] = "Material Master"
                st.session_state['step'] = 2 
                st.rerun()

    else:
        st.markdown("<label class='input-label'>New Project Name</label>", unsafe_allow_html=True)
        new_project_name = st.text_input("New Project Name", placeholder="e.g. Global_Rollout_2024", label_visibility="collapsed")
        
        st.markdown("<label class='input-label' style='margin-top: 16px;'>Primary Master Data Type</label>", unsafe_allow_html=True)
        new_master_type = st.selectbox("Primary Master Data Type", ["Material Master", "Vendor Master"], label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Initialize Environment ➔", type="primary", use_container_width=True):
            if new_project_name in existing_projects:
                st.error("Project name exists. Choose a unique identifier.")
            elif new_project_name:
                try:
                    supabase.table("migration_projects").insert({
                        "project_name": new_project_name, 
                        "master_type": new_master_type
                    }).execute()
                    
                    st.session_state['current_project'] = new_project_name
                    st.session_state['selected_master'] = new_master_type
                    st.session_state['step'] = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")

# --- SCREEN 2: CONFIGURATION DASHBOARD (LIGHT MODE) ---
def render_configuration_dashboard():
    st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)
    
    # --- METADATA HEADER ROW ---
    h_col1, h_col2, h_col3, h_col4 = st.columns([3.5, 3.5, 4, 1])
    
    # 1. Base64 Logo & Brand (Width auto implemented to prevent stretching)
    with h_col1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 14px;">
                <img src="{EXPOUND_LOGO}" style="height: 38px; width: auto; object-fit: contain;" alt="Expound Logo"/>
                <div>
                    <div class="brand-title">Expound Master Data Hub</div>
                    <div class="brand-subtitle">S/4HANA Migration Engine</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    # 2. System Status & Target
    with h_col2:
        st.markdown("""
            <div style="border-left: 1px solid #e2e8f0; padding-left: 1.5rem; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div class="meta-label">Target System & Status</div>
                <div style="display: flex; align-items: center; gap: 12px; margin-top: 2px;">
                    <span class="meta-value">S/4HANA Cloud</span>
                    <span class="status-pill"><span class="status-dot"></span>Connected</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    # 3. Active Project Name (H1 Focus)
    with h_col3:
        st.markdown(f"""
            <div style="text-align: right; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div class="meta-label">Active Project Workspace</div>
                <div class="project-title" style="margin-top: 2px;">📁 {st.session_state.get('current_project', 'None')}</div>
            </div>
        """, unsafe_allow_html=True)
        
    # 4. Secondary Utility Button
    with h_col4:
        if st.button("Change", help="Switch Active Project", use_container_width=True):
            st.session_state['step'] = 1
            st.session_state['current_project'] = None
            if 'generated_xml' in st.session_state:
                del st.session_state['generated_xml']
            st.rerun()
            
    st.markdown("<hr style='margin-top: 1.2rem; margin-bottom: 1.5rem; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # --- MAIN TABS (Master Data Object - Thin SVG Icons) ---
    selected_master = option_menu(
        menu_title=None,
        options=["Material Master", "Vendor Master", "Customer Master"],
        icons=["box-seam", "truck", "people"], 
        default_index=["Material Master", "Vendor Master", "Customer Master"].index(st.session_state['selected_master']),
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "transparent", "border-bottom": "1px solid #e2e8f0", "border-radius": "0px", "margin-bottom": "1.5rem"},
            "icon": {"color": "#64748b", "font-size": "16px"},
            "nav-link": {
                "font-size": "15px", "text-align": "center", "margin": "0px", "color": "#475569", 
                "border-radius": "0px", "padding": "12px 20px"
            },
            "nav-link-selected": {
                "background-color": "transparent", "color": "#0056b3", 
                "border-bottom": "3px solid #0056b3", "font-weight": "700"
            },
        }
    )
    
    if selected_master != st.session_state['selected_master']:
        st.session_state['selected_master'] = selected_master
        st.rerun()

    # --- UNDER DEVELOPMENT GATEKEEPER ---
    if st.session_state['selected_master'] != "Material Master":
        st.markdown(f"""
            <div style="text-align: center; padding: 6rem 2rem; background-color: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1;">
                <h1 style="font-size: 3.5rem; margin-bottom: 0.5rem; color: #94a3b8;">🚧</h1>
                <h3 style="color: #334155; margin-bottom: 0.5rem;">Module Under Development</h3>
                <p style="color: #64748b; font-size: 1.1rem;">The migration logic and templates for <b>{st.session_state['selected_master']}</b> are currently being configured. Please return to Material Master.</p>
            </div>
        """, unsafe_allow_html=True)
        return

    # --- SUB TABS (Workspace Actions - ONLY FOR MATERIAL MASTER) ---
    selected_nav = option_menu(
        menu_title=None,
        options=["Field Mapping", "Rules Definition", "XML Generation"],
        icons=["diagram-3", "file-earmark-ruled", "code-slash"],
        default_index=["Field Mapping", "Rules Definition", "XML Generation"].index(st.session_state['selected_nav']),
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "transparent", "width": "55%", "margin": "0 auto 2.5rem auto"},
            "icon": {"font-size": "14px"},
            "nav-link": {
                "font-size": "13px", "text-align": "center", "margin": "0px 6px", 
                "color": "#64748b", "background-color": "#f1f5f9", "border-radius": "20px", "padding": "8px 16px"
            },
            "nav-link-selected": {
                "background-color": "#eff6ff", "color": "#0056b3", "font-weight": "600", "border": "1px solid #bfdbfe"
            },
        }
    )

    if selected_nav != st.session_state['selected_nav']:
        st.session_state['selected_nav'] = selected_nav
        st.rerun()

    # --- GLOBAL SAP VIEWS DICTIONARY (Pruned for MM & P2P strictly) ---
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
            "Indicator: Storage": False, "Indicator: Purchasing": False, "Material Code": False
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
        "7. Tax Classification (S_MLAN)": {
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
        "8. Plant Data (S_MARC)": {
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
            "Indicator: Purchasing": False, "Indicator: Quality": False
        },
        "9. Storage Locations (S_MARD)": {
            "Product Number": True, "Plant": True, "Storage Location": True, "Storage Bin": False
        },
        "10. MRP Area (S_MRP_AREA)": {
            "Product Number": True, "MRP Area": True, "Plant": True, "MRP Type": False
        }
    }

    # --- MAIN WORKSPACE: FIELD MAPPING ---
    if st.session_state['selected_nav'] == "Field Mapping":
        
        with st.expander("📊 View Saved Mappings Context"):
            try:
                project_mappings = get_all_saved_mappings(st.session_state['current_project'])
                if project_mappings:
                    df_mappings = pd.DataFrame(project_mappings)
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

        st.markdown("---")
        
        selected_view_header = st.selectbox(
            "Select SAP Structure to Configure", 
            options=list(sap_views.keys()),
            index=0
        )
        
        fields_to_render = sap_views[selected_view_header]
        view_name = selected_view_header.split(" (")[0]
        sap_struct = selected_view_header.split("(")[1].replace(")", "")
        
        existing_mappings = get_view_saved_mappings(
            st.session_state['current_project'],
            view_name
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        search_col, scope_col = st.columns([3, 2])

        with search_col:
            search_term = st.text_input(
                "Search field",
                placeholder="🔍 Find a SAP field by name...",
                label_visibility="collapsed"
            )

        with scope_col:
            field_scope = st.radio(
                "Show fields",
                options=["All", "Mandatory only", "Optional only"],
                horizontal=True,
                label_visibility="collapsed"
            )

        field_rows = []
        for field, is_mand in fields_to_render.items():
            if search_term and search_term.lower() not in field.lower():
                continue
            if field_scope == "Mandatory only" and not is_mand:
                continue
            if field_scope == "Optional only" and is_mand:
                continue

            saved_data = existing_mappings.get(field, {})
            saved_mapping = saved_data.get('mapping_type', 'Blank (Default)')
            saved_value = saved_data.get('fixed_value', "") or ""

            field_rows.append({
                "field_name": field,
                "required_flag": "🔴 Mandatory" if is_mand else "⚪ Optional",
                "mapping_type": saved_mapping,
                "fixed_value": saved_value,
            })

        if not field_rows:
            st.info("No fields match the current filter for this SAP view.")
        else:
            field_df = pd.DataFrame(field_rows)
            edited_df = st.data_editor(
                field_df,
                use_container_width=True,
                hide_index=True,
                height=520,
                disabled=["field_name", "required_flag"],
                key=f"mapping_editor_{sap_struct}",
                column_config={
                    "field_name": st.column_config.TextColumn("Source Field ID / Name", disabled=True, width="large"),
                    "required_flag": st.column_config.TextColumn("Req", disabled=True, width="small"),
                    "mapping_type": st.column_config.SelectboxColumn(
                        "Mapping Logic",
                        options=mapping_options,
                        width="medium",
                        required=False,
                    ),
                    "fixed_value": st.column_config.TextColumn(
                        "Value / Rule Definition",
                        width="medium",
                    ),
                },
            )

            configurations_to_save = []
            validation_error = False

            for row in edited_df.to_dict(orient="records"):
                selection = row.get("mapping_type", "Blank (Default)")
                fixed_val = row.get("fixed_value", "")
                field_name = row.get("field_name")
                is_mand = "🔴" in row.get("required_flag", "")

                if is_mand and selection == "Blank (Default)":
                    validation_error = True
                if selection == "Fixed Values" and not str(fixed_val or "").strip():
                    validation_error = True

                configurations_to_save.append({
                    "project_name": st.session_state['current_project'],
                    "sap_structure": sap_struct,
                    "view_name": view_name,
                    "field_name": field_name,
                    "is_mandatory": is_mand,
                    "mapping_type": selection,
                    "fixed_value": fixed_val if selection == "Fixed Values" else None,
                })

        st.markdown("---")
        
        c1, c2, c3 = st.columns([7,2,2])
        with c3:
            if st.button(f"Save Mapping", type="primary", use_container_width=True):
                if validation_error:
                    st.error("Cannot save. Please map all mandatory fields and provide values for 'Fixed Values'.")
                else:
                    try:
                        supabase.table("field_mappings").upsert(
                            configurations_to_save, 
                            on_conflict="project_name,sap_structure,field_name"
                        ).execute()
                        get_all_saved_mappings.clear()
                        get_view_saved_mappings.clear()
                        st.success(f"Mapping logic saved for {view_name}")
                    except Exception as e:
                        st.error(f"Database error during save: {e}")

    # --- UPLOAD FIXED RULES MODULE ---
    elif st.session_state['selected_nav'] == "Rules Definition":
        st.subheader("Rules Definition")
        st.markdown("Download the dynamic template, fill in your mapping logic, and upload the completed dataset.")
        
        current_proj = st.session_state['current_project']
        
        with st.expander("📊 View Saved Rule Datasets"):
            try:
                res_rules = supabase.table("project_fixed_rules").select("rule_data").eq("project_name", current_proj).execute()
                if res_rules.data:
                    saved_rules_df = pd.DataFrame([row['rule_data'] for row in res_rules.data])
                    st.dataframe(saved_rules_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No rules dataset saved for this project.")
            except Exception as e:
                st.error(f"Error loading rules: {e}")

        try:
            response = supabase.table("field_mappings").select("field_name").eq("project_name", current_proj).eq("mapping_type", "Based on Fixed Rules").execute()
            
            standard_keys = ["Product Type", "Product Group", "Plant"]
            rule_fields = []
            for row in response.data:
                fname = row['field_name']
                if fname not in standard_keys and fname not in rule_fields:
                    rule_fields.append(fname)
                    
        except Exception as e:
            st.error(f"Error fetching fields: {e}")
            rule_fields = []
            
        if not rule_fields:
            st.warning("⚠️ No fields mapped to 'Based on Fixed Rules'. Map fields in the Field Mapping tab first.")
        else:
            template_columns = standard_keys + rule_fields
            st.success(f"Found {len(rule_fields)} fields requiring fixed rules logic.")
            
            df_template = pd.DataFrame(columns=template_columns)
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_template.to_excel(writer, index=False, sheet_name='Fixed Rules')
                worksheet = writer.sheets['Fixed Rules']
                for i, col in enumerate(template_columns):
                    worksheet.column_dimensions[worksheet.cell(row=1, column=i+1).column_letter].width = max(len(col) + 2, 15)
            
            st.download_button(
                label="📥 Download Excel Template",
                data=buffer.getvalue(),
                file_name=f"{current_proj}_Fixed_Rules_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.markdown("---")
            
            uploaded_file = st.file_uploader("Upload completed Rules Dataset (Excel)", type=["xlsx", "xls"])
            
            if uploaded_file is not None:
                df_uploaded = pd.read_excel(uploaded_file)
                st.write("##### Pre-Save Verification")
                st.dataframe(df_uploaded, use_container_width=True)
                
                c1, c2, c3 = st.columns([7,2,2])
                with c3:
                    if st.button("💾 Save Rules Dataset", type="primary", use_container_width=True):
                        try:
                            supabase.table("project_fixed_rules").delete().eq("project_name", current_proj).execute()
                            records = df_uploaded.to_dict(orient='records')
                            insert_payload = [{"project_name": current_proj, "rule_data": record} for record in records]
                            
                            if insert_payload:
                                supabase.table("project_fixed_rules").insert(insert_payload).execute()
                                st.success("Dataset saved to project.")
                            else:
                                st.warning("Uploaded file empty. Cleared old rules.")
                        except Exception as e:
                            st.error(f"Error saving rules: {e}")

    # --- UPLOAD & DOWNLOAD XML MODULE ---
    elif st.session_state['selected_nav'] == "XML Generation":
        st.subheader("Payload Generation (XML)")
        st.markdown("Inject raw data into the SAP Migration template based on configured logic.")
        
        current_proj = st.session_state['current_project']
        base_columns = ["Product Number", "Product Description", "Product Type", "Product Group", "Plant"]
        
        try:
            res_mappings = supabase.table("field_mappings").select("*").eq("project_name", current_proj).execute()
            all_mappings = res_mappings.data
            
            user_mapped_fields = []
            for row in all_mappings:
                fname = row['field_name']
                if row['mapping_type'] == "Based on User Input" and fname not in base_columns:
                    if fname not in user_mapped_fields:
                        user_mapped_fields.append(fname)
            
            res_rules = supabase.table("project_fixed_rules").select("rule_data").eq("project_name", current_proj).execute()
            saved_rules = [row['rule_data'] for row in res_rules.data]
        except Exception as e:
            st.error(f"Configuration load error: {e}")
            all_mappings, user_mapped_fields, saved_rules = [], [], []
            
        template_columns = base_columns + user_mapped_fields
        
        st.markdown("##### 1. Source Data Template")
        df_user_template = pd.DataFrame(columns=template_columns)
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_user_template.to_excel(writer, index=False, sheet_name='User Data')
            worksheet = writer.sheets['User Data']
            for i, col in enumerate(template_columns):
                worksheet.column_dimensions[worksheet.cell(row=1, column=i+1).column_letter].width = max(len(col) + 2, 15)
        
        st.download_button(
            label="📥 Download Upload Template",
            data=buffer.getvalue(),
            file_name=f"{current_proj}_Data_Upload_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        
        st.markdown("---")
        
        st.markdown("##### 2. Execute Transformation")
        uploaded_file = st.file_uploader("Upload raw data (Excel)", type=["xlsx", "xls"], key="user_data_upload")
        
        if uploaded_file is not None:
            df_uploaded = pd.read_excel(uploaded_file)
            st.write(f"Detected **{len(df_uploaded)}** material records.")
            st.dataframe(df_uploaded, use_container_width=True)
            
            c1, c2 = st.columns([8, 2])
            with c2:
                if st.button("▶ Execute Migration Logic", type="primary", use_container_width=True):
                    template_path = os.path.join("templates", "Source data for Product.xml")
                    
                    if not os.path.exists(template_path):
                        st.error("Missing core XML template in `/templates/` directory.")
                    else:
                        with st.spinner("Processing data mappings..."):
                            final_sap_data = {}
                            user_materials = df_uploaded.to_dict(orient='records')
                            
                            for mat_index, material in enumerate(user_materials):
                                matched_rule = {}
                                for rule in saved_rules:
                                    if (str(rule.get("Product Type", "")) == str(material.get("Product Type", "")) and
                                        str(rule.get("Product Group", "")) == str(material.get("Product Group", "")) and
                                        str(rule.get("Plant", "")) == str(material.get("Plant", ""))):
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
                                    if mapping_type in ["Blank (Default)", "Keep Blank"]:
                                        resolved_value = ""
                                    elif mapping_type == "Fixed Values":
                                        resolved_value = map_config.get('fixed_value', "")
                                    elif mapping_type == "Based on Fixed Rules":
                                        resolved_value = matched_rule.get(field_name, "")
                                    elif mapping_type == "Based on User Input" or field_name in base_columns:
                                        resolved_value = material.get(field_name, "")
                                        
                                    if pd.isna(resolved_value) or resolved_value is None:
                                        resolved_value = ""
                                        
                                    final_sap_data[view_name][mat_index][field_name] = resolved_value
                            
                            with open(template_path, "r", encoding="utf-8") as f:
                                xml_content = f.read()
                                
                            for view_key, rows_list in final_sap_data.items():
                                sheet_name = view_key.split(". ", 1)[-1]
                                sheet_start_tag = f'<Worksheet ss:Name="{sheet_name}"'
                                
                                if sheet_start_tag in xml_content:
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
                                    
                                    def update_row_count(match):
                                        old_count = int(match.group(1))
                                        new_count = old_count + num_new_rows
                                        return f'ss:ExpandedRowCount="{new_count}"'
                                    
                                    inside_table = re.sub(r'ss:ExpandedRowCount="(\d+)"', update_row_count, inside_table, count=1)
                                    xml_content = before_sheet + sheet_start_tag + inside_table + sheet_xml_rows + "</Table>" + after_table
                                    
                            st.session_state['generated_xml'] = xml_content
                            st.success("Payload structured successfully.")

            if 'generated_xml' in st.session_state:
                st.download_button(
                    label="📥 Download SAP XML Payload",
                    data=st.session_state['generated_xml'],
                    file_name=f"{current_proj}_Migration_Payload.xml",
                    mime="application/xml"
                )

def main():
    if st.session_state.get('step') == 1:
        render_project_setup()
    else:
        render_configuration_dashboard()

if __name__ == "__main__":
    main()