import google.generativeai as genai
from google.cloud import aiplatform
from config import settings
import json

# Initialize the services
aiplatform.init(project=settings.PROJECT_ID, location=settings.LOCATION)
genai.configure(api_key=settings.API_KEY)

# Default model names
DEFAULT_MODEL = 'gemini-1.5-pro-latest'

def get_gemini_model(model_name=None):
    """Get a Gemini generative model"""
    model_name = model_name or settings.generative_model_name or DEFAULT_MODEL
    return genai.GenerativeModel(model_name)

def generate_content(prompt, model_name=None, temperature=0.7, system_instruction=None):
    """Generate content using Gemini with enhanced controls"""
    model = get_gemini_model(model_name)
    
    generation_config = {
        "temperature": temperature,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
    
    # Use the chat format which allows for system instructions
    if system_instruction:
        response = model.generate_content(
            contents=[
                {"role": "system", "parts": [system_instruction]},
                {"role": "user", "parts": [prompt]}
            ],
            generation_config=generation_config
        )
    else:
        response = model.generate_content(
            contents=prompt,
            generation_config=generation_config
        )
    
    if hasattr(response, 'text'):
        return response.text
    return str(response)

def analyze_sentiment_with_gemini(text):
    """Analyze sentiment using Gemini with structured output"""
    system_instruction = """
    You are an expert sentiment analyzer specialized in venture capital and startup pitches.
    Provide detailed, nuanced analysis focusing on confidence, knowledge depth, and pitch effectiveness.
    """
    
    prompt = f"""
    Analyze the sentiment and qualities of this venture capital interview response:
    
    "{text}"
    
    Return a JSON object with the following structure:
    {{
      "score": [number between -1 and 1],
      "confidence_level": [number between 0 and 10],
      "knowledge_depth": [number between 0 and 10],
      "key_strengths": [array of up to 3 strengths],
      "key_weaknesses": [array of up to 3 weaknesses],
      "explanation": [brief explanation of your analysis]
    }}
    
    Respond with ONLY the JSON object, no other text.
    """
    
    try:
        response = generate_content(prompt, temperature=0.1, system_instruction=system_instruction)
        # Clean the response to ensure it's valid JSON
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:-3]  # Remove markdown code block markers
        
        result = json.loads(response)
        return result
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        # Fallback
        return {
            "score": 0, 
            "confidence_level": 5,
            "knowledge_depth": 5,
            "key_strengths": [],
            "key_weaknesses": [],
            "explanation": "Basic sentiment analysis."
        }

def generate_feedback_with_examples(transcript, is_detailed=False):
    """Generate interview feedback using few-shot examples"""
    system_instruction = """
    You are an expert venture capital interviewer with 15+ years of experience evaluating startups and founders.
    Your feedback is insightful, actionable, and balanced, highlighting both strengths and areas for improvement.
    Focus on both content (business understanding, market knowledge) and delivery (confidence, clarity).
    """
    
    # Sample VC interview Q&A with expert feedback examples for few-shot learning
    examples = """
    Example 1:
    Question: "How do you plan to acquire customers?"
    Response: "We'll use social media and maybe some ads. People seem to like our product so far."
    Expert Feedback: This response lacks specificity and data. A stronger answer would include: target CAC, specific channels with proven traction, metrics from existing acquisition efforts, and a clear understanding of the customer journey.
    
    Example 2:
    Question: "What's your total addressable market?"
    Response: "Our TAM is $4.2B based on industry reports from Gartner and our analysis of the 340,000 SMBs that fit our ideal customer profile. We've validated demand with a 12% conversion rate in our initial pilot with 200 businesses."
    Expert Feedback: Excellent response with specific market size supported by credible sources and early validation metrics. The candidate demonstrates both market research and the ability to convert that potential into actual customers.
    """
    
    detail_level = "comprehensive" if is_detailed else "concise"
    
    prompt = f"""
    Review this venture capital interview transcript and provide {detail_level} feedback:
    
    {transcript}
    
    Based on similar interviews, here are examples of strong and weak responses with expert feedback:
    {examples}
    
    Provide your feedback in the following format:
    
    OVERALL ASSESSMENT:
    [1-2 paragraphs summarizing the candidate's overall performance]
    
    STRENGTHS:
    - [Key strength 1]
    - [Key strength 2]
    - [Key strength 3]
    
    AREAS FOR IMPROVEMENT:
    - [Improvement area 1]
    - [Improvement area 2]
    - [Improvement area 3]
    
    ACTIONABLE ADVICE:
    [3-5 specific recommendations to improve pitch effectiveness]
    """
    
    try:
        return generate_content(prompt, temperature=0.7, system_instruction=system_instruction)
    except Exception as e:
        print(f"Error generating feedback: {e}")
        return "We couldn't generate detailed feedback at this time. Please try again later."

def generate_cv_questions_enhanced(cv_text):
    """Generate personalized interview questions based on CV with advanced prompting"""
    system_instruction = """
    You are an expert venture capital interviewer who specializes in identifying founders' strengths and weaknesses.
    Your questions are tailored to the candidate's background, probing for both domain expertise and entrepreneurial mindset.
    Focus on the candidate's ability to execute, their market understanding, and their vision.
    """
    
    prompt = f"""
    Based on this resume/CV text, generate 5 personalized venture capital interview questions:
    
    {cv_text}
    
    Each question should follow this pattern:
    1. Be specific to the candidate's background
    2. Probe for both knowledge and strategic thinking
    3. Require concrete examples or data
    
    For each question, include:
    - The question itself
    - Why this question is relevant to this specific candidate
    - What a strong answer would demonstrate
    
    Format each question as a simple string in a list, without explanations or numbering.
    """
    
    try:
        questions_text = generate_content(prompt, temperature=0.8, system_instruction=system_instruction)
        
        # Parse the response to extract just the questions
        import re
        questions = re.findall(r'"([^"]*)"', questions_text)
        if not questions:
            questions = [line.strip() for line in questions_text.split('\n') if line.strip() and line.strip().endswith('?')]
        
        return questions[:5]  # Return up to 5 questions
    except Exception as e:
        print(f"Error generating CV questions: {e}")
        return [
            "Based on your experience at {}, what key metrics did you track to measure success?",
            "How would you apply your background in {} to build a scalable startup?",
            "What's the biggest market opportunity you've identified from your work so far?",
            "How does your experience in {} give you unique insights for this venture?",
            "What specific challenges from your past roles are you best equipped to handle as a founder?"
        ]
