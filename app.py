"""
Evals Demo: Customer Pain Point Extractor
"""
import streamlit as st
import sqlite3
from datetime import datetime
from claude_api import call_claude, evaluate_response

# Page config
st.set_page_config(
    page_title="Evals Demo",
    page_icon="🎯",
    layout="wide"
)

# Initialize session state
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = "You are a helpful assistant."

# Sarah's persona
SARAH_PERSONA = {
    "name": "Sarah",
    "age": 32,
    "context": "Has a wedding to attend in 2 weeks",
    "goal": "Find a dress that fits well and looks elegant",
    "pain_point": "Usually between sizes (struggles with fit)",
    "time_constraint": "Needs it in 2 weeks (some buffer for returns)",
    "budget": "Willing to spend up to $150",
    "behaviors": [
        "Reads reviews carefully, especially about sizing",
        "Anxious about online shopping",
        "Values honest opinions over marketing fluff",
        "Will return if it doesn't fit perfectly"
    ]
}

# Sidebar - Persona and API Key
with st.sidebar:
    st.header("👤 Sarah's Persona")
    st.markdown(f"**Age:** {SARAH_PERSONA['age']}")
    st.markdown(f"**Context:** {SARAH_PERSONA['context']}")
    st.markdown(f"**Goal:** {SARAH_PERSONA['goal']}")
    st.markdown(f"**Pain Point:** {SARAH_PERSONA['pain_point']}")
    st.markdown(f"**Budget:** {SARAH_PERSONA['budget']}")
    
    st.markdown("**Behaviors:**")
    for behavior in SARAH_PERSONA['behaviors']:
        st.markdown(f"- {behavior}")
    
    st.markdown("---")
    
    st.header("🔑 API Key")
    llm_api_key = st.text_input("Anthropic API Key:", type="password", 
                            help="Get your API key from console.anthropic.com")

# Main content
st.title("🎯 Evals Demo")

# Two columns - System Prompt and Chat
col1, col2 = st.columns(2)

with col1:
    st.subheader("System Prompt")
    system_prompt = st.text_area(
        "",
        value=st.session_state.system_prompt,
        height=400,
        label_visibility="collapsed"
    )
    
    # Update session state if changed
    if system_prompt != st.session_state.system_prompt:
        st.session_state.system_prompt = system_prompt

with col2:
    st.subheader("Chat")
    
    # Chat messages container
    chat_container = st.container(height=400)
    
    with chat_container:
        # Initialize chat history
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question..."):
        if not llm_api_key:
            st.error("Please enter your API key in the sidebar")
        else:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Call Claude API
            result = call_claude(
                api_key=llm_api_key,
                system_prompt=st.session_state.system_prompt,
                user_message=prompt,
                review_context=None
            )
            
            if result['success']:
                response = result['response']
            else:
                response = f"Error: {result['error']}"
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

# Sample feedbacks table
st.markdown("---")
st.subheader("Sample Customer Reviews")

# Get some reviews from database
import pandas as pd

conn = sqlite3.connect('data/evals_demo.db')

print("Fetching reviews from database..., ", conn)
# Fetch reviews
df = pd.read_sql_query("""
    SELECT id, clothing_id, age, rating, department_name, 
           substr(review_text, 1, 150) || '...' as review_preview
    FROM feedback_submissions 
    LIMIT 10
""", conn)

conn.close()

# Display as table
st.dataframe(df, use_container_width=True, hide_index=True)