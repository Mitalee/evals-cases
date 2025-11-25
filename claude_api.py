"""
Claude API integration for evaluation runs
"""
import anthropic
from typing import Dict, List

def call_claude(
    api_key: str,
    system_prompt: str,
    user_message: str,
    review_context: Dict = None,
    model: str = "claude-sonnet-4-20250514"
) -> Dict:
    """
    Call Claude API with given prompts
    
    Args:
        api_key: Anthropic API key
        system_prompt: System prompt configuration
        user_message: User's question
        review_context: Optional review data to include as context
        model: Claude model to use
        
    Returns:
        Dict with response text and metadata
    """
    client = anthropic.Anthropic(api_key=api_key)
    
    # Build the full user message with context
    full_message = user_message
    
    if review_context:
        context_text = f"""
Here's a customer review about the dress you're being asked about:

Rating: {review_context.get('rating')} stars
Customer Age: {review_context.get('age')}
Review: {review_context.get('review_text')}
Department: {review_context.get('department')}
Recommended: {'Yes' if review_context.get('recommended') else 'No'}

Now, please answer the following question:

{user_message}
"""
        full_message = context_text
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": full_message}
            ]
        )
        
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
