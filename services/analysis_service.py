import asyncio
from utils.gemini_utils import generate_content, analyze_sentiment_with_gemini, generate_feedback_with_examples
from config import settings

async def analyze_single_response(question, actual, expected):
    """Analyze a single interview response using Gemini with improved prompting"""
    system_instruction = """
    You are an expert VC investor and pitch coach with extensive experience evaluating founders.
    Your feedback is specific, actionable, and balanced, focusing on both substance and delivery.
    """
    
    prompt = f"""
    Evaluate this venture capital interview response:
    
    Question: {question}
    Expected answer criteria: {expected}
    Candidate's actual answer: {actual}
    
    Provide detailed feedback on:
    1. How well the answer meets investor expectations (scale 1-10)
    2. Strength of the business understanding demonstrated
    3. Use of specific metrics, data points, or concrete examples
    4. Clarity and confidence of communication
    5. Specific improvements that would make the answer more compelling
    
    Be precise about what worked well and what specific changes would strengthen the response.
    """
    
    return generate_content(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.4
    )

async def analyze_responses(responses, expected, questions):
    """Analyze responses concurrently with enhanced methods"""
    tasks = []
    for i, (question, actual, expected_ans) in enumerate(zip(questions, responses, expected)):
        tasks.append(analyze_single_response(question, actual, expected_ans))
    
    individual_feedback = await asyncio.gather(*tasks)
    
    # Combine individual feedback
    combined_feedback = ""
    for i, feedback in enumerate(individual_feedback):
        combined_feedback += f"\n\n== Question {i+1}: {questions[i]} ==\n{feedback}"
    
    # Generate overall summary with more specific guidance
    system_instruction = """
    You are a senior venture capital partner providing feedback to a founder after a pitch meeting.
    Your assessment is honest but constructive, highlighting specific strengths while providing
    actionable feedback on areas for improvement. Focus on both business understanding and communication.
    """
    
    summary_prompt = f"""
    Based on this detailed VC interview feedback, provide a structured assessment of the candidate's performance:
    {combined_feedback}
    
    Format your feedback as follows:

    OVERALL ASSESSMENT:
    [One paragraph executive summary with an overall score from 1-10]
    
    KEY STRENGTHS:
    - [Specific strength 1 with example]
    - [Specific strength 2 with example]
    - [Specific strength 3 with example]
    
    PRIORITY AREAS FOR IMPROVEMENT:
    - [Specific improvement 1 with actionable advice]
    - [Specific improvement 2 with actionable advice]
    - [Specific improvement 3 with actionable advice]
    
    INVESTOR READINESS:
    [Assessment of how ready this founder is to pitch to actual investors]
    
    NEXT STEPS:
    [3 concrete action items to improve pitch effectiveness]
    """
    
    summary_response = generate_content(
        prompt=summary_prompt,
        system_instruction=system_instruction,
        temperature=0.5
    )
    
    return {
        "detailed_feedback": combined_feedback,
        "summary": summary_response
    }

def analyze_sentiment(text):
    """Enhanced sentiment analysis using the improved Gemini implementation"""
    return analyze_sentiment_with_gemini(text)

def generate_interview_feedback(session):
    """Generate comprehensive feedback for the entire interview using few-shot examples"""
    transcript = session.get_full_transcript()
    
    # Extract questions and responses
    questions = []
    responses = []
    dialogue = ""
    
    for item in transcript:
        if item["speaker"] == "interviewer":
            questions.append(item["text"])
            dialogue += f"Interviewer: {item['text']}\n\n"
        elif item["speaker"] == "candidate":
            responses.append(item["text"])
            dialogue += f"Candidate: {item['text']}\n\n"
    
    # Generate enhanced feedback using our improved utility
    feedback = generate_feedback_with_examples(dialogue, is_detailed=True)
    
    return {
        "session_id": session.session_id,
        "feedback": feedback,
        "questions": questions,
        "responses": responses
    }
