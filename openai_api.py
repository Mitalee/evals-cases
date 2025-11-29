"""
OpenAI API integration for evaluation runs
"""
from openai import OpenAI
import sqlite3
from typing import Dict, List
import json

def call_openai(
    api_key: str,
    system_prompt: str,
    user_message: str,
    review_context: Dict = None,
    model: str = "gpt-4o-mini",
    use_tool: bool = False,
    conversation_history: List[Dict] = None
) -> Dict:
    """
    Call OpenAI API with given prompts
    
    Args:
        api_key: OpenAI API key
        system_prompt: System prompt configuration
        user_message: User's question
        review_context: Optional review data to include as context
        model: OpenAI model to use (gpt-4o-mini is the cheapest)
        use_tool: Whether to enable database query tool
        conversation_history: Optional list of previous messages for context
        
    Returns:
        Dict with response text and metadata
    """
    client = OpenAI(api_key=api_key)
    
    # Build the full user message
    full_message = user_message
    
    try:
        # Define tools if enabled
        tools = []
        if use_tool:
            tools = [{
                "type": "function",
                "function": {
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
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {
                                "type": "string",
                                "description": "SQL query to run against the feedback_submissions table"
                            }
                        },
                        "required": ["sql_query"]
                    }
                }
            }]

        # Build messages array
        messages = []
        
        # Add system message
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": full_message})

        # Call OpenAI
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": 2000
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # print("OPENAI API: Calling with model:", model)
        print("OPENAI API: kwargs:", kwargs)

        response = client.chat.completions.create(**kwargs)
        
        # Check if tool was called
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            
            # Execute the SQL query
            conn = sqlite3.connect('data/evals_demo.db')
            cursor = conn.cursor()
            results = None
            try:
                args = json.loads(tool_call.function.arguments)
                cursor.execute(args["sql_query"])
                results = cursor.fetchall()
                tool_result_text = "\n".join(str(row) for row in results)
            except Exception as e:
                tool_result_text = f"Error executing query: {e}"
                results = []
            finally:
                conn.close()
            
            # print("OPENAI API: Tool results:", results)
            
            # Send tool results back to OpenAI for a natural language response
            messages.append(response.choices[0].message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result_text
            })
            
            # Get OpenAI's final response with the tool results
            final_response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000
            )
            
            return {
                "success": True,
                "response": final_response.choices[0].message.content,
                "model": model,
                "tokens": {
                    "input": response.usage.prompt_tokens + final_response.usage.prompt_tokens,
                    "output": response.usage.completion_tokens + final_response.usage.completion_tokens
                }
            }

        return {
            "success": True,
            "response": response.choices[0].message.content,
            "model": model,
            "tokens": {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
