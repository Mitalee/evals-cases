"""
Claude API integration for evaluation runs
"""
import anthropic
import sqlite3
from typing import Dict, List

def call_claude(
    api_key: str,
    system_prompt: str,
    user_message: str,
    review_context: Dict = None,
    model: str = "claude-haiku-4-5-20251001",
    use_tool: bool = False,
    conversation_history: List[Dict] = None
) -> Dict:
    """
    Call Claude API with given prompts
    
    Args:
        api_key: Anthropic API key
        system_prompt: System prompt configuration
        user_message: User's question
        review_context: Optional review data to include as context
        model: Claude model to use
        use_tool: Whether to enable database query tool
        conversation_history: Optional list of previous messages for context
        
    Returns:
        Dict with response text and metadata
    """
    client = anthropic.Anthropic(api_key=api_key)
    
    # Build the full user message (no additional review context)
    full_message = user_message
    
    try:
        # Define tools if enabled
        tools = []
        if use_tool:
            """
            The problem: Claude doesn't know the correct schema! It's guessing column names.
            The fix: Update the tool description to include the schema:
            """
            tools = [{
                        "name": "query_reviews",
                        "description": """Query the customer reviews database to get information about products, reviews, sizing, ratings, etc.

                    Available columns in feedback_submissions table:
                    - id: Review ID (primary key)
                    - clothing_id: Product identifier
                    - age: Customer age
                    - title: Review title
                    - review_text: Full review content
                    - rating: Star rating (1-5)
                    - recommended_ind: Whether customer recommends (0 or 1)
                    - positive_feedback_count: Number of helpful votes
                    - division_name: Product division
                    - department_name: Department (Tops, Dresses, Bottoms, etc.)
                    - class_name: Product class
                    - created_at: Timestamp

                    Example queries:
                    - Get reviews for a product: SELECT * FROM feedback_submissions WHERE clothing_id = 1094
                    - Filter by age: SELECT * FROM feedback_submissions WHERE clothing_id = 1094 AND age BETWEEN 30 AND 40
                    - Get average rating: SELECT AVG(rating) FROM feedback_submissions WHERE clothing_id = 1094""",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "sql_query": {
                                    "type": "string",
                                    "description": "SQL query to run against the feedback_submissions table"
                                }
                            },
                            "required": ["sql_query"]
                        }
                    }]

        # Build messages array
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": full_message})

        # Call Claude
        kwargs = {
            "model": model,
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": messages
        }
        
        if tools:
            kwargs["tools"] = tools

        print("CLAUDE API: kwargs:", kwargs)

        message = client.messages.create(**kwargs)
        
        # Debug: print the initial Claude response for inspection
        print("CLAUDE API: Claude initial response:", message)
        
        # If tool usage is detected, handle it and send results back to Claude
        if message.stop_reason == "tool_use":
            tool_use = next(block for block in message.content if block.type == "tool_use")
            # Execute the SQL query
            conn = sqlite3.connect('data/evals_demo.db')
            cursor = conn.cursor()
            results = None
            try:
                cursor.execute(tool_use.input["sql_query"])
                results = cursor.fetchall()
                print("CLAUDE API: Tool execution results:", results)
                tool_result_text = "\n".join(str(row) for row in results)
            except Exception as e:
                tool_result_text = f"Error executing query: {e}"
                results = []
            finally:
                conn.close()
            
            print("CLAUDE API: Tool results:", results)
            
            # Send tool results back to Claude for a natural language response
            messages.append({
                "role": "assistant",
                "content": message.content
            })
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": tool_result_text
                    }
                ]
            })
            
            # Get Claude's final response with the tool results
            final_message = client.messages.create(
                model=model,
                max_tokens=2000,
                system=system_prompt,
                messages=messages,
                tools=tools
            )
            
            print("CLAUDE API: Claude final response:", final_message)
            
            return {
                "success": True,
                "response": final_message.content[0].text,
                "model": model,
                "tokens": {
                    "input": message.usage.input_tokens + final_message.usage.input_tokens,
                    "output": message.usage.output_tokens + final_message.usage.output_tokens
                }
            }

        return {
            "success": True,
            "response": message.content[0].text,
            "model": model,
            "tokens": {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def evaluate_response(
    response: str,
    must_include: List[str],
    question_type: str
) -> Dict:
    """
    Simple evaluation of response quality
    
    Args:
        response: AI's response text
        must_include: List of elements that should be present
        question_type: Type of question being evaluated
        
    Returns:
        Dict with pass/fail and reasoning
    """
    response_lower = response.lower()
    
    # Check if key elements are present
    missing_elements = []
    for element in must_include:
        # Simple keyword matching (can be improved with LLM-as-judge)
        element_keywords = element.lower().split()
        found = any(keyword in response_lower for keyword in element_keywords)
        if not found:
            missing_elements.append(element)
    
    passes = len(missing_elements) == 0
    
    return {
        "passes": passes,
        "missing_elements": missing_elements,
        "found_elements": [e for e in must_include if e not in missing_elements],
        "response_length": len(response),
        "evaluation_type": "rule_based"  # Could be "llm_judge" later
    }
