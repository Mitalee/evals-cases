"""
Evals Demo: Customer Pain Point Extractor
"""
import streamlit as st
import os
from dotenv import load_dotenv
import sqlite3
from claude_api import call_claude
from openai_api import call_openai

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
    st.session_state.system_prompt = ""#"You are a helpful assistant."
if 'eval_results' not in st.session_state:
    st.session_state.eval_results = {}  # {question_id: {"passed": bool, "details": dict}}
if 'game_complete' not in st.session_state:
    st.session_state.game_complete = False
if 'current_question_id' not in st.session_state:
    st.session_state.current_question_id = None
if 'try_counter' not in st.session_state:
    st.session_state.try_counter = {}  # {question_id: try_number}
if 'selected_brand' not in st.session_state:
    st.session_state.selected_brand = "Anthropic"

# Evaluation Questions
EVAL_QUESTIONS = [
    {
        "id": 1,
        "question": "I have a wedding in 2 weeks. Should I order clothing ID 1094?",
        "context": {"clothing_id": 1094},
        "ground_truth": "HIGH RISK: sizing issues, quality concerns. Sarah is anxious about online shopping and hates returns.",
        "assertions": [
            {
                "check": "includes_buy_link",
                "description": "Response includes a buy link in format https://santra.com/clothing/{id}",
                "keywords": ["https://santra.com/clothing/", "santra.com/clothing"]
            },
            {
                "check": "tailored_to_sarah",
                "description": "Response is personalized - references Sarah by name OR addresses her specific context",
                "keywords": [
                    "sarah",
                    "you're", "your", "you mentioned", "I know you",  # Personal pronouns showing awareness
                    "wedding", "upcoming", "special event",  # Her event
                    "anxious", "anxiety", "concerned", "worried",  # Her emotions
                    "return", "returns", "exchange",  # Her aversion
                    "between sizes", "fit", "sizing",  # Her struggle
                    "professional", "work", "presentation",  # Her needs
                    "budget", "spend", "$150"  # Her constraint
                ]
            }
        ],
        "pass_criteria": "Both assertions must pass",
        "prompt_improvement": "Add Sarah's context to your system prompt. Reference her by name and address her specific concerns (anxiety about online shopping, return aversion, fit struggles)."
    },
    {
        "id": 2,
        "question": "Does clothing ID 829 have quality issues?",
        "context": {"clothing_id": 829},
        "ground_truth": "Yes, quality issues exist. Sarah needs reliable clothing for work presentations.",
        "assertions": [
            {
                "check": "includes_buy_link",
                "description": "Response includes a buy link in format https://santra.com/clothing/{id}",
                "keywords": ["https://santra.com/clothing/", "santra.com/clothing"]
            },
            {
                "check": "tailored_to_sarah",
                "description": "Response is personalized - references Sarah by name OR addresses her specific context",
                "keywords": [
                    "sarah",
                    "you're", "your", "you mentioned", "I know you",  # Personal pronouns showing awareness
                    "wedding", "upcoming", "special event",  # Her event
                    "anxious", "anxiety", "concerned", "worried",  # Her emotions
                    "return", "returns", "exchange",  # Her aversion
                    "between sizes", "fit", "sizing",  # Her struggle
                    "professional", "work", "presentation",  # Her needs
                    "budget", "spend", "$150"  # Her constraint
                ]
            }
        ],
        "pass_criteria": "Both assertions must pass",
        "prompt_improvement": "Connect the quality issues to Sarah's specific needs (professional settings, work presentations). Show you understand her context."
    },
    {
        "id": 3,
        "question": "I'm between sizes (usually 8-10). Which size should I order for clothing ID 1094?",
        "context": {"clothing_id": 1094},
        "ground_truth": "Runs 2-4 sizes small. Sarah struggles with fit and needs confident guidance.",
        "assertions": [
            {
                "check": "includes_buy_link",
                "description": "Response includes a buy link in format https://santra.com/clothing/{id}",
                "keywords": ["https://santra.com/clothing/", "santra.com/clothing"]
            },
            {
                "check": "tailored_to_sarah",
                "description": "Response is personalized - references Sarah by name OR addresses her specific context",
                "keywords": [
                    "sarah",
                    "you're", "your", "you mentioned", "I know you",  # Personal pronouns showing awareness
                    "wedding", "upcoming", "special event",  # Her event
                    "anxious", "anxiety", "concerned", "worried",  # Her emotions
                    "return", "returns", "exchange",  # Her aversion
                    "between sizes", "fit", "sizing",  # Her struggle
                    "professional", "work", "presentation",  # Her needs
                    "budget", "spend", "$150"  # Her constraint
                ]
            }
        ],
        "pass_criteria": "Both assertions must pass",
        "prompt_improvement": "Acknowledge Sarah's fit struggles and give her confident, specific advice. Reduce her anxiety with personalized guidance."
    }
]

# System prompts are separate - you test different prompts against the same questions
SYSTEM_PROMPTS = {
    "empty": "",
    "basic": "You are a shopping assistant. Help customers make purchase decisions.",
    "sales_driven": "You are a shopping assistant. Your goal is to drive purchases. Always include a purchase link: https://santra.com/clothing/{id}",
    "customer_focused": "You are a shopping assistant. Your goal is customer satisfaction. Include purchase links only for items you confidently recommend. For risky items, suggest alternatives with links."
}
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
    
    st.header("🤖 LLM Provider & API Key")
    st.session_state.selected_brand = st.radio(
        "Select Provider:",
        ["Anthropic", "OpenAI"],
        index=0 if st.session_state.selected_brand == "Anthropic" else 1
    )
    
    if st.session_state.selected_brand == "Anthropic":
        llm_api_key = st.text_input("Anthropic API Key:", type="password", 
                                help="Get your API key from console.anthropic.com")
    else:
        llm_api_key = st.text_input("OpenAI API Key:", type="password", 
                                help="Get your API key from platform.openai.com")
    
    st.markdown("---")

# Main content
st.title("🎯 Evals - Clothing Recommendations")

def evaluate_response_rule_based(response: str, question_id: int, scenario: str = "neutral") -> dict:
    """
    Evaluate a response using rule-based keyword matching.
    
    Args:
        response: The AI's response text
        question_id: The ID of the question being evaluated
        scenario: Which scenario to evaluate against (neutral, sales_driven, customer_satisfaction)
        
    Returns:
        dict with 'passed' (bool) and 'details' (dict of assertion results)
    """
    # Find the question
    question_data = next((q for q in EVAL_QUESTIONS if q["id"] == question_id), None)
    if not question_data:
        return {"passed": False, "details": {}, "error": "Question not found"}
    
    response_lower = response.lower()
    assertion_results = {}
    
    # Handle new scenario-based structure
    if "scenarios" in question_data:
        if scenario not in question_data["scenarios"]:
            return {"passed": False, "details": {}, "error": f"Scenario '{scenario}' not found"}
        
        assertions = question_data["scenarios"][scenario]["assertions"]
    # Handle old structure (direct assertions)
    elif "assertions" in question_data:
        assertions = question_data["assertions"]
    else:
        return {"passed": False, "details": {}, "error": "No assertions found in question"}
    
    # Check each assertion
    for assertion in assertions:
        check_name = assertion["check"]
        keywords = assertion.get("keywords", [])
        
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
tab1, tab2 = st.tabs(["📚 Case Study", "🎯 Evals"])
# tab2, = st.tabs(["🎯 Evals"])  # Comma unpacks the single-element tuple

#Tab 1: Case Study - Sample Reviews
with tab1:
    st.header("🎮 The Challenge")
    
    st.markdown("""
    ## Build an AI Shopping Assistant That Actually Helps Customers Buy
    
    **The Problem:** Your AI analyzes reviews perfectly but forgets to help customers take action.
    
    **Your Mission:** Make it commercial-ready in 3 prompts.
    
    ---
    
    ### ⚡ Quick Setup
    
    - **Platform:** Santra.com (e-commerce clothing)
    - **Customer:** Sarah, 32, needs a dress for wedding in 2 weeks
    - **AI Tool:** Can query customer reviews database
    - **Your Job:** Write prompts that pass evals
    
    ---
    
    ### 🎯 Win Condition: Pass 2 Evals
    
    **Eval 1: Commercial Behavior**  
    ✅ Include buy link: `https://santra.com/clothing/{id}`
    
    **Eval 2: Personalization**  
    ✅ Address Sarah by name OR reference her concerns
    
    ---
    
    ### 🎮 How to Play
    
    1. Ask question → Both evals fail ❌❌
    2. Add buy link instruction to prompt → One passes ✅❌
    3. Add Sarah's context to prompt → Both pass ✅✅
    4. **You win!** 🎉
    
    💡 **Pro tip:** Sarah's profile is in the sidebar
    
    ---
    
    ### 📊 Sample Data
    """)
    
    # Show sample data
    import pandas as pd
    conn = sqlite3.connect('data/evals_demo.db')
    
    df = pd.read_sql_query("""
        SELECT clothing_id, rating, age, department_name, 
               substr(review_text, 1, 100) || '...' as review_preview
        FROM feedback_submissions 
        WHERE clothing_id IN (1094, 829)
        LIMIT 6
    """, conn)
    
    conn.close()
    
    st.dataframe(df, width='stretch', hide_index=True)
    
    st.markdown("""
    ---
    
    **Ready?** → **Evals** tab 🚀
    """)

# Tab 2: Evals - Main Interface
with tab2:
    # Chat input handler
    def handle_chat_input():
        print("🔍 DEBUG: handle_chat_input called!")
        prompt = st.session_state.chat_input_val
        print(f"🔍 DEBUG: prompt = {prompt}")
        if prompt:
            if not llm_api_key:
                print("🔍 ERROR: No API key provided!")
                st.error("Please enter your API key in the sidebar")
            else:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Prepare conversation history if save_context is enabled
                conversation_history = None
                if save_context and len(st.session_state.messages) > 1:
                    # Pass all messages except the one we just added (we'll send it separately)
                    conversation_history = st.session_state.messages[:-1]
                
                print(f"🔍 save_context={save_context}, conversation_history={'None' if conversation_history is None else f'{len(conversation_history)} messages'}")
                
                # Build system prompt with user memory if enabled
                effective_system_prompt = st.session_state.system_prompt
                if use_user_memory:
                    user_memory_context = f"""
                        You are helping {SARAH_PERSONA['name']}, a {SARAH_PERSONA['age']}-year-old customer who:
                        - {SARAH_PERSONA['context']}
                        - {SARAH_PERSONA['pain_point']}
                        - Budget: {SARAH_PERSONA['budget']}
                        - Goal: {SARAH_PERSONA['goal']}

                        Customer behaviors:
                        {chr(10).join(f'- {behavior}' for behavior in SARAH_PERSONA['behaviors'])}

                        Tailor your recommendations to her specific situation, risk tolerance, and constraints."""
                    effective_system_prompt = st.session_state.system_prompt + user_memory_context
                
                # print("🔍 Conversation history:", conversation_history)
                # print("🔍 User message:", prompt)
                # print("🔍 System prompt:", effective_system_prompt)
                # print("🔍 Use DB tool:", use_db_tool)
                
                # Call appropriate API based on selected brand
                if st.session_state.selected_brand == "Anthropic":
                    # print("🔍 CALLING CLAUDE API")
                    result = call_claude(
                        api_key=llm_api_key,
                        system_prompt=effective_system_prompt,
                        user_message=prompt,
                        review_context=None,
                        use_tool=use_db_tool,
                        conversation_history=conversation_history
                    )
                else:  # OpenAI
                    # print("🔍 CALLING OPENAI API")
                    result = call_openai(
                        api_key=llm_api_key,
                        system_prompt=effective_system_prompt,
                        user_message=prompt,
                        review_context=None,
                        use_tool=use_db_tool,
                        conversation_history=conversation_history
                    )
                
                if result['success']:
                    response = result['response']
                    # print("🔍 SUCCESS - Response preview:", response[:200] if len(response) > 200 else response)
                else:
                    response = f"Error: {result['error']}"
                    # print("🔍 ERROR Response:", response)
                
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                print("🔍 Total messages in history:", len(st.session_state.messages))
                
                # Run evaluation if this was an eval question
                if st.session_state.current_question_id is not None:
                    # Increment try counter for this question
                    q_id = st.session_state.current_question_id
                    if q_id not in st.session_state.try_counter:
                        st.session_state.try_counter[q_id] = 0
                    st.session_state.try_counter[q_id] += 1
                    
                    eval_result = evaluate_response_rule_based(
                        response, 
                        st.session_state.current_question_id
                    )
                    # Add try number to the result
                    eval_result['try_number'] = st.session_state.try_counter[q_id]
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
        use_user_memory = st.checkbox("Enable User Memory (Sarah's Persona)", value=False,
                                help="Add Sarah's persona and preferences to the system prompt for personalized recommendations")
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
                                    
                                    # Show try number
                                    try_num = result.get('try_number', 1)
                                    st.markdown(f"**📝 Try #{try_num}**")
                                    st.markdown("---")
                                    
                                    # Get assertions for this question (handle both old and new structure)
                                    if "scenarios" in q:
                                        scenario = result.get("scenario", "neutral")
                                        assertions = q["scenarios"][scenario]["assertions"]
                                    else:
                                        assertions = q.get("assertions", [])
                                    
                                    if result["passed"]:
                                        st.success("✅ Passed - All assertions met!")
                                    else:
                                        st.error("❌ Failed - Some assertions not met")
                                    
                                    # Show ALL assertions with their status (passed or failed)
                                    if "details" in result:
                                        for check, passed in result["details"].items():
                                            # Find the description for this check
                                            assertion = next((a for a in assertions if a["check"] == check), None)
                                            if assertion:
                                                if passed:
                                                    st.success(f"✅ {assertion['description']}")
                                                else:
                                                    st.error(f"❌ {assertion['description']}")
                                    
                                    # Show improvement tip if available and failed
                                    if not result["passed"] and "prompt_improvement" in q:
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
        
        st.button("Send", on_click=handle_chat_input, width='stretch')

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
            st.markdown(f"{'✓' if use_user_memory else '✗'} User Memory")
            st.markdown(f"{'✓' if save_context else '✗'} Save Context")
            st.markdown(f"**Eval Method:** Rule-based")
        
        st.markdown("---")
        st.info("💡 Take a screenshot of this results screen to share your score!")
        
        if st.button("🔄 Play Again"):
            st.session_state.eval_results = {}
            st.session_state.game_complete = False
            st.session_state.messages = []
            st.session_state.try_counter = {}
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
                         width='stretch')

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p style='font-size: 0.9rem;'>Making AI quality a habit ❤️</p>
        <p style='font-size: 0.8rem;'>Powered by Claude AI • Anthropic • Visual Studio Code • GitHub Copilot</p>
    </div>
    """,
    unsafe_allow_html=True
)