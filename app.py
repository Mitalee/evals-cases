"""
Evals Demo: Customer Pain Point Extractor
"""
import streamlit as st
import os
from dotenv import load_dotenv
import sqlite3
from claude_api import call_claude

# Load environment variables
load_dotenv()

# Test print statement on app load
# print("🚀 APP LOADED - Print statements are working!")

# Page config
st.set_page_config(
    page_title="Evals - AI Recommendation Agent",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.stTextArea textarea {
    font-size: 1.2rem !important;
}
[data-testid="stSidebar"] {
    font-size: 0.8rem !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-size: 1rem !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] li {
    font-size: 0.8rem !important;
}
/* Ensure dataframe font is small */
.stDataFrame {
    font-size: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = "You are a helpful assistant."
if 'eval_results' not in st.session_state:
    st.session_state.eval_results = {}  # {question_id: {"passed": bool, "details": dict}}
if 'game_complete' not in st.session_state:
    st.session_state.game_complete = False
if 'current_question_id' not in st.session_state:
    st.session_state.current_question_id = None

# Evaluation Questions
EVAL_QUESTIONS = [
    {
        "id": 1,
        "question": "I have a wedding in 2 weeks and need a dress. I'm looking at clothing ID 1094 that has mixed reviews about sizing. Should I order it?",
        "context": {"clothing_id": 1094},
        "assertions": [
            {
                "check": "uses_specific_data",
                "description": "Response includes specific data from reviews (review count, ratings, or customer details)",
                "keywords": ["8 reviews", "8 customers", "4.1", "4.12", "3 out of 8", "three reviewers", "size 6", "size 10", "size 14", "38", "44", "34G"]
            },
            # {
            #     "check": "identifies_risk",
            #     "description": "Response identifies this as a HIGH RISK purchase",
            #     "keywords": ["high risk", "risky", "risk"]
            # },
            {
                "check": "mentions_sizing_issue",
                "description": "Response mentions sizing issues (runs small, inconsistent, etc.)",
                "keywords": ["runs small", "ran small", "running small", "fit small", "fits small", "sizing issues"]
            },
            {
                "check": "mentions_returns",
                "description": "Response warns about returns/exchanges timeline",
                "keywords": ["return", "exchange", "arrive in time", "too late"]
            }
            # {
            #     "check": "gives_specific_advice",
            #     "description": "Response suggests ordering 2 sizes or finding in-store alternative",
            #     "keywords": ["2 sizes", "two sizes", "multiple sizes", "both sizes", "in-store", "in store", "physical store"]
            # }
        ],
        "pass_criteria": "All 5 assertions must pass",
        "prompt_improvement": "When advising on time-sensitive purchases, analyze delivery risks and sizing consistency. If reviews mention sizing issues, recommend ordering multiple sizes or having a backup plan."
    },
    {
        "id": 2,
        "question": "I'm 35 years old and looking at clothing ID 1094. What do other customers around my age (30-40) think about it?",
        "context": {"clothing_id": 1094, "age_range": [30, 40]},
        "ground_truth": "4 customers aged 30-40 reviewed it. Ratings: 38yo(2★), 39yo(5★), 39yo(5★), 33yo(4★). Average: 4.0 stars. Mixed experiences - one found it too small, others loved the fit.",
        "assertions": [
            {
                "check": "filters_by_age",
                "description": "Response shows it filtered reviews by age 30-40",
                "keywords": ["age", "30", "35", "40", "customers your age", "similar age", "age group"]
            },
            {
                "check": "provides_count",
                "description": "Response mentions 4 customers in that age range",
                "keywords": ["4", "four", "customers", "reviewers"]
            },
            {
                "check": "summarizes_feedback",
                "description": "Response summarizes ratings and experiences from those customers",
                "keywords": ["rating", "stars", "mixed", "loved", "small", "fit"]
            }
        ],
        "pass_criteria": "All 3 assertions must pass",
        "prompt_improvement": "When users mention their age, filter and analyze reviews from customers in a similar age range (±5 years). State how many customers in that age group reviewed the item and summarize their specific feedback."
    },
    {
        "id": 3,
        "question": "Does clothing ID 829 have quality issues? What are customers saying?",
        "context": {"clothing_id": 829},
        "ground_truth": "6 reviews, 3.17★ average (lowest among items with 5+ reviews). Quality issues: seam through bust looks bad (2★), color changed after dry cleaning (3★), couldn't zip around ribcage (3★), sleeves too loose despite sizing up (3★).",
        "assertions": [
            {
                "check": "identifies_issues",
                "description": "Response mentions specific quality issues from reviews",
                "keywords": ["seam", "bust", "color", "dry clean", "fabric", "zip", "ribcage", "sleeves", "quality"]
            },
            {
                "check": "references_low_rating",
                "description": "Response acknowledges the low average rating (3.17)",
                "keywords": ["3.1", "3.2", "low", "below average", "mixed", "poor"]
            },
            {
                "check": "lists_complaints",
                "description": "Response lists multiple specific complaints from customers",
                "keywords": ["seam", "color changed", "sizing", "fit", "issue"]
            }
        ],
        "pass_criteria": "All 3 assertions must pass",
        "prompt_improvement": "When asked about quality issues, analyze low-rated reviews (≤3 stars) and list specific problems customers mentioned. Acknowledge when an item has below-average ratings and be honest about product weaknesses."
    }
]

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
    
    st.markdown("---")

# Main content
st.title("🎯 Evals Demo")

def evaluate_response_rule_based(response: str, question_id: int) -> dict:
    """
    Evaluate a response using rule-based keyword matching.
    
    Args:
        response: The AI's response text
        question_id: The ID of the question being evaluated
        
    Returns:
        dict with 'passed' (bool) and 'details' (dict of assertion results)
    """
    # Find the question
    question_data = next((q for q in EVAL_QUESTIONS if q["id"] == question_id), None)
    if not question_data:
        return {"passed": False, "details": {}, "error": "Question not found"}
    
    response_lower = response.lower()
    assertion_results = {}
    
    # Check each assertion
    for assertion in question_data["assertions"]:
        check_name = assertion["check"]
        keywords = assertion["keywords"]
        
        # Check if any keyword is present in the response
        found = any(keyword.lower() in response_lower for keyword in keywords)
        assertion_results[check_name] = found
    
    # All assertions must pass
    all_passed = all(assertion_results.values())
    
    return {
        "passed": all_passed,
        "details": assertion_results
    }

def set_question(question_text, question_id):
    """Set the question in the chat input and track which question was asked."""
    st.session_state.chat_input_val = question_text
    st.session_state.current_question_id = question_id

# Create tabs
# tab1, tab2 = st.tabs(["📚 Case Study", "🎯 Evals"])
tab2, = st.tabs(["🎯 Evals"])  # Comma unpacks the single-element tuple

# Tab 1: Case Study - Sample Reviews
# with tab1:
    # st.header("Sample Customer Reviews")
    # st.markdown("""
    # Study this schema and sample data before moving to the Evals section. 
    # This database contains customer reviews for clothing items.
    # """)
    
    # # Get some reviews from database
    # import pandas as pd
    
    # conn = sqlite3.connect('data/evals_demo.db')
    
    # # print("Fetching reviews from database..., ", conn)
    # # Fetch reviews
    # df = pd.read_sql_query("""
    #     SELECT id, clothing_id, age, rating, department_name, 
    #            substr(review_text, 1, 150) || '...' as review_preview
    #     FROM feedback_submissions 
    #     LIMIT 10
    # """, conn)
    
    # conn.close()
    
    # # Display as table
    # st.dataframe(df, use_container_width=True, hide_index=True)

# Tab 2: Evals - Main Interface
with tab2:
    # Chat input handler
    def handle_chat_input():
        print("🔍 DEBUG: handle_chat_input called!")
        prompt = st.session_state.chat_input_val
        print(f"🔍 DEBUG: prompt = {prompt}")
        if prompt:
            if not llm_api_key:
                st.error("Please enter your API key in the sidebar")
            else:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Prepare conversation history if save_context is enabled
                conversation_history = None
                if save_context and len(st.session_state.messages) > 1:
                    # Pass all messages except the one we just added (we'll send it separately)
                    conversation_history = st.session_state.messages[:-1]
                
                # print("🔍 Conversation history:", conversation_history)
                # print("🔍 User message:", prompt)
                # print("🔍 System prompt:", st.session_state.system_prompt)
                # print("🔍 Use DB tool:", use_db_tool)
                # print("🔍 CALLING CLAUDE API")
                # Call Claude API
                result = call_claude(
                    api_key=llm_api_key,
                    system_prompt=st.session_state.system_prompt,
                    user_message=prompt,
                    review_context=None,
                    use_tool=use_db_tool,
                    conversation_history=conversation_history
                )
                
                if result['success']:
                    response = result['response']
                else:
                    response = f"Error: {result['error']}"
                    print("🔍 ERROR Response:", response)
                
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Run evaluation if this was an eval question
                if st.session_state.current_question_id is not None:
                    eval_result = evaluate_response_rule_based(
                        response, 
                        st.session_state.current_question_id
                    )
                    st.session_state.eval_results[st.session_state.current_question_id] = eval_result
                    
                    # Check if game is complete (all questions answered)
                    if len(st.session_state.eval_results) == len(EVAL_QUESTIONS):
                        st.session_state.game_complete = True
                    
                    # Reset current question ID
                    st.session_state.current_question_id = None
                
                # Clear input
                st.session_state.chat_input_val = ""

    # Two columns - System Prompt and Chat
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("System Prompt")
        system_prompt = st.text_area(
            "System Prompt",
            value=st.session_state.system_prompt,
            height=400,
            label_visibility="collapsed"
        )
        
        # Character counter
        st.caption(f"Characters: {len(system_prompt)}")
        
        # Update session state if changed
        if system_prompt != st.session_state.system_prompt:
            st.session_state.system_prompt = system_prompt

        st.markdown("---")
        use_db_tool = st.checkbox("Enable Database Query Tool", value=False, 
                                help="Allow Claude to query the reviews database for better answers")
        save_context = st.checkbox("Save context", value=False,
                                help="Send full conversation history to Claude for context")
        use_llm_judge = st.checkbox("Use LLM-as-Judge", value=False, disabled=True,
                                help="Use Claude to evaluate responses (coming soon)")

    with col2:
        st.subheader("Chat")
        
        # Chat messages container
        chat_container = st.container(height=400)
        
        with chat_container:
            # Initialize chat history
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            
            # Display chat messages
            for idx, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    # Show eval result if this is an assistant message that was evaluated
                    if message["role"] == "assistant":
                        # Check if this message has an eval result
                        # We need to match this to a question - check if idx-1 was a user message
                        # that matches one of our eval questions
                        if idx > 0:
                            user_msg = st.session_state.messages[idx - 1]["content"]
                            for q in EVAL_QUESTIONS:
                                if q["question"] == user_msg and q["id"] in st.session_state.eval_results:
                                    result = st.session_state.eval_results[q["id"]]
                                    if result["passed"]:
                                        st.success("✅ Passed")
                                    else:
                                        st.error("❌ Failed")
                                        # Show specific failure reasons
                                        if "details" in result:
                                            for check, passed in result["details"].items():
                                                if not passed:
                                                    # Find the description for this check
                                                    assertion = next((a for a in q["assertions"] if a["check"] == check), None)
                                                    if assertion:
                                                        st.warning(f"⚠️ Missing: {assertion['description']}")
                                        
                                        if "prompt_improvement" in q:
                                            st.info(f"💡 **Tip:** {q['prompt_improvement']}")
                                    break
        
        # Chat input - using text_area for better visibility of long questions
        st.text_area(
            "Ask a question...", 
            key="chat_input_val", 
            on_change=handle_chat_input,
            label_visibility="collapsed",
            placeholder="Ask a question...",
            height=80
        )
        
        st.button("Send", on_click=handle_chat_input, use_container_width=True)

    # Evaluation Questions Section
    st.markdown("---")
    
    # Show results screen if game is complete
    if st.session_state.game_complete:
        st.success("🎉 Evaluation Complete!")
        
        # Calculate score
        passed_count = sum(1 for result in st.session_state.eval_results.values() if result["passed"])
        total_count = len(EVAL_QUESTIONS)
        
        # Create a nice results display
        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("Score", f"{passed_count}/{total_count}")
            if passed_count == total_count:
                st.markdown("### ✅ Perfect Score!")
            elif passed_count > 0:
                st.markdown("### 📊 Good Effort!")
            else:
                st.markdown("### 💪 Keep Trying!")
        
        with col_b:
            st.metric("System Prompt Length", f"{len(st.session_state.system_prompt)} chars")
        
        with col_c:
            st.markdown("**Tools Used:**")
            st.markdown(f"{'✓' if use_db_tool else '✗'} Database Query Tool")
            st.markdown(f"{'✓' if save_context else '✗'} Save Context")
            st.markdown(f"**Eval Method:** Rule-based")
        
        st.markdown("---")
        st.info("💡 Take a screenshot of this results screen to share your score!")
        
        if st.button("🔄 Play Again"):
            st.session_state.eval_results = {}
            st.session_state.game_complete = False
            st.session_state.messages = []
            st.rerun()
            
    else:
        # Show evaluation questions
        st.subheader("📝 Evaluation Questions")
        st.markdown("Click a question to populate the chat:")
        
        # Create a container for the questions
        with st.container():
            for q_data in EVAL_QUESTIONS:
                q_id = q_data["id"]
                q_text = q_data["question"]
                
                # Show status if answered, but keep enabled for retries
                label = q_text
                if q_id in st.session_state.eval_results:
                    result = st.session_state.eval_results[q_id]
                    status = "✅" if result["passed"] else "❌"
                    label = f"{status} {q_text}"
                
                st.button(label, key=f"q_{q_id}", 
                         on_click=set_question, args=(q_text, q_id), 
                         use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p style='font-size: 0.9rem;'>Built with ❤️ by Mitalee</p>
        <p style='font-size: 0.8rem;'>Powered by Claude AI • Anthropic • Gemini Pro • Visual Studio Code</p>
    </div>
    """,
    unsafe_allow_html=True
)