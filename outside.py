import os
import json
import google.generativeai as genai
from typing import List, Dict, Any, Optional

# Configure Gemini API key - replace with your actual key if needed
API_KEY = "AIzaSyCNjAzI3AYUDHlcPuXbZ42fQFhzxmZ4qrw"
genai.configure(api_key=API_KEY)

class FeedbackDemo:
    def __init__(self):
        """Initialize the feedback demo with models"""
        self.model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
    
    def generate_content(self, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.4) -> str:
        """Generate content using Gemini model with enhanced prompting"""
        try:
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            # Build a conversation with system prompt if provided
            if system_instruction:
                response = self.model.generate_content(
                    [system_instruction, prompt],
                    generation_config=generation_config
                )
            else:
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            
            return response.text
        except Exception as e:
            print(f"Error generating content: {e}")
            return f"Error: {str(e)}"
    
    def analyze_single_response(self, question: str, actual: str, expected: str) -> str:
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
        
        return self.generate_content(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.4
        )
    
    def analyze_sentiment_with_gemini(self, text: str) -> Dict[str, Any]:
        """Enhanced sentiment analysis with structured JSON output"""
        system_instruction = """
        You are an expert in sentiment analysis specialized in analyzing venture capital interviews.
        Analyze the text and return a structured JSON response containing sentiment scores and analysis.
        """
        
        prompt = f"""
        Analyze the sentiment, confidence level, and communication quality in this interview response:
        
        "{text}"
        
        Provide your analysis as a structured JSON with the following fields:
        - sentiment: (positive/neutral/negative)
        - confidence_score: (1-10)
        - key_sentiment_drivers: [list of specific phrases/elements that drive the sentiment]
        - communication_quality: (1-10)
        - improvement_suggestions: [specific actionable suggestions]
        """
        
        response = self.generate_content(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.2
        )
        
        # Try to extract JSON from the response
        try:
            # Find JSON content between curly braces
            json_str = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            # Fallback in case JSON parsing fails
            return {
                "sentiment": "neutral",
                "confidence_score": 5,
                "key_sentiment_drivers": ["Unable to parse response"],
                "communication_quality": 5,
                "improvement_suggestions": ["Error processing response"],
                "raw_response": response
            }
    
    def generate_feedback_with_examples(self, full_interview_text: str, is_detailed: bool = False) -> Dict[str, Any]:
        """Generate comprehensive feedback for the entire interview using few-shot examples"""
        system_instruction = """
        You are a senior VC partner and expert pitch coach who provides detailed, structured feedback to founders.
        Your analysis is data-driven, specific, and focuses on both technical/business understanding and communication.
        Format your response as a structured JSON object.
        """
        
        detail_level = "highly detailed" if is_detailed else "concise"
        
        prompt = f"""
        Analyze this venture capital interview transcript and provide {detail_level} feedback:
        
        {full_interview_text}
        
        Return your analysis as a structured JSON with the following fields:
        - overall_score: (1-10)
        - strengths: [list of 3-5 specific strengths with examples from the transcript]
        - areas_for_improvement: [list of 3-5 specific areas to improve with actionable advice]
        - business_understanding: {{score: (1-10), comments: "detailed assessment"}}
        - communication_quality: {{score: (1-10), comments: "detailed assessment"}}
        - investor_readiness: {{score: (1-10), comments: "assessment of readiness to pitch to real investors"}}
        - next_steps: [3-5 specific actionable recommendations]
        
        Be specific, data-driven, and actionable in your feedback. Reference specific parts of the conversation.
        """
        
        response = self.generate_content(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.4
        )
        
        # Try to extract JSON from the response
        try:
            # Find JSON content between curly braces
            json_str = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            # Fallback in case JSON parsing fails
            return {
                "overall_score": 5,
                "strengths": ["Unable to parse response"],
                "areas_for_improvement": ["Error processing feedback"],
                "business_understanding": {"score": 5, "comments": "Error processing feedback"},
                "communication_quality": {"score": 5, "comments": "Error processing feedback"},
                "investor_readiness": {"score": 5, "comments": "Error processing feedback"},
                "next_steps": ["Review the interview transcript manually"],
                "raw_response": response
            }

def main():
    """Main function to demonstrate feedback capabilities"""
    demo = FeedbackDemo()
    
    print("=" * 80)
    print("VC INTERVIEW FEEDBACK DEMO")
    print("=" * 80)
    
    # Example 1: Single Response Analysis
    print("\n1. SINGLE RESPONSE ANALYSIS EXAMPLE\n")
    
    question = "How does your past experience prepare you for venture capital?"
    expected = "Should demonstrate understanding of VC, connect past experiences with relevant skills, and show passion for startups."
    actual = "I worked at Google for 5 years as a product manager where I launched several products. I think my experience working with engineers and understanding tech will help me in VC."
    
    print(f"Question: {question}")
    print(f"Response: {actual}")
    print("\nFeedback:")
    feedback = demo.analyze_single_response(question, actual, expected)
    print(feedback)
    
    # Example 2: Sentiment Analysis
    print("\n" + "=" * 80)
    print("\n2. SENTIMENT ANALYSIS EXAMPLE\n")
    
    sample_response = "I believe my background in fintech gives me an edge in evaluating financial startups. At PayPal, I led a team that increased transaction volume by 30% through data-driven optimizations. I've also personally invested in three early-stage startups and helped them build their go-to-market strategies."
    
    print(f"Sample response: {sample_response}")
    print("\nSentiment analysis:")
    sentiment = demo.analyze_sentiment_with_gemini(sample_response)
    print(json.dumps(sentiment, indent=2))
    
    # Example 3: Full Interview Feedback
    print("\n" + "=" * 80)
    print("\n3. FULL INTERVIEW FEEDBACK EXAMPLE\n")
    
    # Sample interview transcript
    interview_transcript = """
    Interviewer: Tell me about your background and why you're interested in venture capital.
    
    Candidate: I've spent the last four years working at a Series B fintech startup where I led product. Before that, I was at Microsoft in their cloud division. I'm interested in VC because I enjoy working with early-stage founders and have a good eye for product-market fit based on my experience.
    
    Interviewer: How would you evaluate an early-stage SaaS company?
    
    Candidate: I'd look at their monthly recurring revenue growth, customer acquisition costs, and retention metrics. I'd also evaluate the team's background and their understanding of the market. The product needs to solve a real pain point, and there should be a clear path to scaling.
    
    Interviewer: What's a recent technology trend you're excited about?
    
    Candidate: I'm watching the developments in AI-powered developer tools closely. Companies like GitHub Copilot are showing how AI can dramatically improve developer productivity. I think we'll see more specialized coding assistants for different domains, which could change how software is built.
    """
    
    print("Sample interview transcript provided (shortened for demo)")
    print("\nComprehensive feedback:")
    complete_feedback = demo.generate_feedback_with_examples(interview_transcript, is_detailed=True)
    print(json.dumps(complete_feedback, indent=2))

if __name__ == "__main__":
    main() 