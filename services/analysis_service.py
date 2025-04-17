import asyncio
from utils.gemini_utils import generate_content, analyze_sentiment_with_gemini, generate_feedback_with_examples
from config import settings
import os
import logging
import json
import traceback
from google.generativeai import GenerativeModel

logger = logging.getLogger(__name__)

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
    """
    Analyze sentiment of an interview response
    """
    try:
        # Try to use our cloud manager
        try:
            from utils.google_cloud import cloud_manager
            model = cloud_manager.get_genai_model()
            
            if model is None:
                logger.warning("Gemini model not available, using fallback mechanism")
                return {"score": 0.0, "magnitude": 0.0, "sentiment": "neutral"}
        except Exception as e:
            logger.error(f"Error getting Gemini model: {e}")
            return {"score": 0.0, "magnitude": 0.0, "sentiment": "neutral"}
        
        # Setup prompt for sentiment analysis
        prompt = f"""
        Analyze the sentiment of the following interview response. 
        Return a JSON object with:
        - score (float between -1.0 and 1.0, where -1.0 is very negative and 1.0 is very positive)
        - magnitude (float between 0.0 and 1.0, indicating the strength of the sentiment)
        - sentiment (string: "positive", "negative", or "neutral")
        
        Response to analyze: "{text}"
        
        JSON response:
        """
        
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract JSON from response
        try:
            # Try to parse response as JSON
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].strip()
            else:
                json_text = response_text.strip()
                
            sentiment_data = json.loads(json_text)
            
            # Ensure we have all expected fields
            if "score" not in sentiment_data:
                sentiment_data["score"] = 0.0
            if "magnitude" not in sentiment_data:
                sentiment_data["magnitude"] = 0.0
            if "sentiment" not in sentiment_data:
                sentiment_data["sentiment"] = "neutral"
                
            return sentiment_data
        except Exception as e:
            logger.error(f"Error parsing sentiment response: {e}")
            return {"score": 0.0, "magnitude": 0.0, "sentiment": "neutral"}
            
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        logger.error(traceback.format_exc())
        return {"score": 0.0, "magnitude": 0.0, "sentiment": "neutral"}

def generate_interview_feedback(session):
    """
    Generate comprehensive feedback based on the interview session
    """
    try:
        # Try to use our cloud manager
        try:
            from utils.google_cloud import cloud_manager
            model = cloud_manager.get_genai_model()
            
            if model is None:
                logger.warning("Gemini model not available, using fallback mechanism")
                return {"feedback": "Unable to generate feedback at this time. Service unavailable."}
        except Exception as e:
            logger.error(f"Error getting Gemini model: {e}")
            return {"feedback": "Unable to generate feedback at this time. Service unavailable."}
        
        # Extract transcript from session
        transcript = session.get_full_transcript()
        
        if not transcript:
            return {"feedback": "No interview data available to generate feedback."}
        
        # Format transcript for the model
        formatted_transcript = []
        for item in transcript:
            speaker = "Interviewer" if item["speaker"] == "interviewer" else "Candidate"
            formatted_transcript.append(f"{speaker}: {item['text']}")
        
        transcript_text = "\n".join(formatted_transcript)
        
        # Setup prompt for feedback generation
        prompt = f"""
        You are an expert VC interview coach. Review the following interview transcript and provide comprehensive feedback.
        
        INTERVIEW TRANSCRIPT:
        {transcript_text}
        
        Provide detailed feedback on:
        1. Overall impression and communication style
        2. Strengths demonstrated
        3. Areas for improvement
        4. Key points that were well articulated
        5. Specific suggestions for better responses
        
        Format the feedback as a cohesive essay that would be helpful to the candidate.
        """
        
        response = model.generate_content(prompt, temperature=0.2)
        
        return {"feedback": response.text}
            
    except Exception as e:
        logger.error(f"Error generating interview feedback: {e}")
        logger.error(traceback.format_exc())
        return {"feedback": "An error occurred while generating feedback. Please try again later."}

def generate_interview_questions(cv_text=None, previous_questions=None, previous_responses=None):
    """
    Generate interview questions based on CV and previous interaction
    """
    try:
        # Try to use our cloud manager
        try:
            from utils.google_cloud import cloud_manager
            model = cloud_manager.get_genai_model()
            
            if model is None:
                logger.warning("Gemini model not available, using fallback mechanism")
                return ["Tell me about your background and experience?"]
        except Exception as e:
            logger.error(f"Error getting Gemini model: {e}")
            return ["Tell me about your background and experience?"]
        
        # If no CV or previous questions, generate standard VC interview questions
        if not cv_text and (not previous_questions or not previous_responses):
            prompt = """
            Generate 5 challenging venture capital interview questions that would be asked to a startup founder.
            Return only the questions as a JSON array of strings.
            """
            
            response = model.generate_content(prompt)
            
            try:
                # Try to parse response as JSON
                response_text = response.text
                if "```json" in response_text:
                    json_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_text = response_text.split("```")[1].strip()
                else:
                    json_text = response_text.strip()
                    
                questions = json.loads(json_text)
                return questions if isinstance(questions, list) else [questions[0]]
            except:
                # Fallback in case parsing fails
                return ["Tell me about your startup idea?", 
                        "How do you plan to generate revenue?", 
                        "What is your go-to-market strategy?"]
        
        # If CV is provided, generate questions based on CV
        elif cv_text:
            prompt = f"""
            You are a venture capital investor interviewing a potential founder.
            
            CV/RESUME:
            {cv_text}
            
            Generate 5 specific and challenging questions based on this CV that will help evaluate:
            1. The founder's expertise and experience
            2. Their understanding of their industry and market
            3. Their ability to execute and scale a business
            
            Return only the questions as a JSON array of strings.
            """
            
            response = model.generate_content(prompt)
            
            try:
                # Try to parse response as JSON
                response_text = response.text
                if "```json" in response_text:
                    json_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_text = response_text.split("```")[1].strip()
                else:
                    json_text = response_text.strip()
                    
                questions = json.loads(json_text)
                return questions if isinstance(questions, list) else [questions[0]]
            except:
                # Fallback in case parsing fails
                return ["Based on your resume, tell me more about your experience in your industry?", 
                        "How has your background prepared you for founding a startup?"]
        
        # If previous interaction is provided, generate follow-up questions
        elif previous_questions and previous_responses:
            # Format previous interaction
            conversation = []
            for i in range(min(len(previous_questions), len(previous_responses))):
                conversation.append(f"Question: {previous_questions[i]}")
                conversation.append(f"Response: {previous_responses[i]}")
            
            conversation_text = "\n".join(conversation)
            
            prompt = f"""
            You are a venture capital investor conducting an in-depth interview.
            
            PREVIOUS INTERACTION:
            {conversation_text}
            
            Generate 3 follow-up questions that dig deeper based on the responses given.
            The questions should challenge the candidate to provide more specific details and demonstrate their expertise.
            
            Return only the questions as a JSON array of strings.
            """
            
            response = model.generate_content(prompt)
            
            try:
                # Try to parse response as JSON
                response_text = response.text
                if "```json" in response_text:
                    json_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_text = response_text.split("```")[1].strip()
                else:
                    json_text = response_text.strip()
                    
                questions = json.loads(json_text)
                return questions if isinstance(questions, list) else [questions[0]]
            except:
                # Fallback in case parsing fails
                return ["Can you elaborate more on your last response?", 
                        "What specific metrics or KPIs would you use to measure success?"]
                
    except Exception as e:
        logger.error(f"Error generating interview questions: {e}")
        logger.error(traceback.format_exc())
        return ["Tell me about your background and experience?"]
