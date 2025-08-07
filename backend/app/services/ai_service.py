import google.generativeai as genai
from app.core.config import settings
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        try:
            # Configure Gemini API
            logger.debug("Initializing Gemini API with key...")
            genai.configure(api_key=settings.gemini_api_key)
            
            # Initialize model
            logger.debug("Creating GenerativeModel instance...")
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # Changed to gemini-1.5-flash as it's the stable version
            logger.debug("AI Service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AI Service: {str(e)}")
            self.model = None

    async def summarize_notes(self, text: str, max_length: int = 500) -> Dict[str, Any]:
        """Summarize long text notes using AI."""
        try:
            prompt = f"""
            Please summarize the following text in a clear, concise manner. 
            The summary should be no more than {max_length} words and should capture the key points and main ideas.
            
            Text to summarize:
            {text}
            
            Please provide the summary in the following JSON format:
            {{
                "summary": "the summarized text",
                "key_points": ["point 1", "point 2", "point 3"],
                "word_count": number_of_words_in_summary
            }}
            
            Respond only with the JSON, no additional text.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Handle possible formatting issues in the response
            try:
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]  # Remove ```json and ``` markers
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]  # Remove ``` markers
                    
                response_text = response_text.strip()
                result = json.loads(response_text)
                
                # Validate required fields
                if not all(key in result for key in ["summary", "key_points", "word_count"]):
                    raise ValueError("Missing required fields in AI response")
                    
                return {
                    "success": True,
                    "data": result
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {response_text}")
                raise ValueError(f"Invalid JSON format in AI response: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing AI response: {response_text}")
                raise ValueError(f"Error processing AI response: {str(e)}")
        except Exception as e:
            logger.error(f"Error summarizing notes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_quiz(self, text: str, num_questions: int = 5) -> Dict[str, Any]:
        """Generate quiz questions from text using AI."""
        try:
            if not self.model:
                raise ValueError("AI model not initialized. Check if GEMINI_API_KEY is set correctly.")

            if not text or not text.strip():
                raise ValueError("Input text cannot be empty")

            prompt = f"""
            Based on the following text, generate {num_questions} multiple choice questions.
            For each question:
            1. Generate a clear, specific question
            2. Create 4 distinct answer options labeled A, B, C, D
            3. Mark one option as correct
            4. Provide a brief explanation for why the correct answer is right
            
            Text to generate questions from:
            {text}
            
            Format your response as a valid JSON object with this exact structure:
            {{
                "questions": [
                    {{
                        "question": "What is...?",
                        "options": [
                            "A) First option",
                            "B) Second option", 
                            "C) Third option",
                            "D) Fourth option"
                        ],
                        "correct_answer": "A) First option",
                        "explanation": "This is correct because..."
                    }}
                ],
                "total_questions": {num_questions}
            }}

            Requirements:
            1. Each option MUST start with its letter (A, B, C, or D) followed by a closing parenthesis
            2. The correct_answer MUST exactly match one of the options including the letter prefix
            3. Generate exactly {num_questions} questions
            4. Do not use any markdown formatting
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Handle possible markdown code blocks in response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            response_text = response_text.strip()
            
            try:
                result = json.loads(response_text)
                
                # Validate required fields and structure
                if "questions" not in result or not isinstance(result["questions"], list):
                    raise ValueError("Invalid response format: missing or invalid 'questions' array")
                
                if "total_questions" not in result:
                    result["total_questions"] = len(result["questions"])
                
                # Validate each question
                for q in result["questions"]:
                    if not all(key in q for key in ["question", "options", "correct_answer", "explanation"]):
                        raise ValueError("Invalid question format: missing required fields")
                        
                    # Validate options
                    if not isinstance(q["options"], list) or len(q["options"]) != 4:
                        raise ValueError("Invalid options format: must be an array of 4 items")
                        
                    # Validate option format (A), B), C), D))
                    for i, option in enumerate(q["options"]):
                        expected_prefix = f"{chr(65 + i)}) "  # A), B), C), D)
                        if not option.startswith(expected_prefix):
                            q["options"][i] = f"{expected_prefix}{option.lstrip('ABCD) ')}"
                    
                    # If correct_answer doesn't have the letter prefix, add it
                    if not any(q["correct_answer"] == opt for opt in q["options"]):
                        # Try to find the option without the prefix
                        clean_answer = q["correct_answer"].lstrip('ABCD) ')
                        for opt in q["options"]:
                            if clean_answer in opt:
                                q["correct_answer"] = opt
                                break
                        else:
                            raise ValueError("Invalid correct_answer: must match one of the options")
                
                return {
                    "success": True,
                    "data": result
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {response_text}")
                raise ValueError(f"Invalid JSON format in AI response: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Validation error in generate_quiz: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_mindmap(self, topic: str, subtopics: List[str] = None) -> Dict[str, Any]:
        """Create a mind map structure for a topic using AI."""
        try:
            if not self.model:
                raise ValueError("AI model not initialized. Check if GEMINI_API_KEY is set correctly.")

            if not topic or not topic.strip():
                raise ValueError("Topic cannot be empty")

            base_prompt = """
            Create a comprehensive mind map structure. The response must be a valid JSON object.
            Include 3-5 main branches, each with 2-4 subtopics.
            Each subtopic should have 2-3 key details or facts.
            
            Response format must be exactly:
            {
                "topic": "main topic",
                "branches": [
                    {
                        "name": "main branch name",
                        "subtopics": [
                            {
                                "name": "subtopic name",
                                "details": ["detail 1", "detail 2"]
                            }
                        ]
                    }
                ]
            }
            
            Do not use any markdown formatting in the response.
            Respond only with the JSON object, no additional text or explanations.
            """
            
            if not subtopics:
                prompt = f"""
                {base_prompt}
                
                Generate a mind map for this topic: "{topic}"
                """
            else:
                prompt = f"""
                {base_prompt}
                
                Generate a mind map for the topic "{topic}" that incorporates these subtopics: {', '.join(subtopics)}
                Organize the provided subtopics into logical branches and add additional relevant subtopics as needed.
                """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            try:
                # Handle possible markdown code blocks in response
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]  # Remove ```json and ``` markers
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]  # Remove ``` markers
                
                response_text = response_text.strip()
                result = json.loads(response_text)
                
                # Validate required fields and structure
                if not isinstance(result, dict):
                    raise ValueError("Invalid response format: root must be an object")
                
                if "topic" not in result or not isinstance(result["topic"], str):
                    raise ValueError("Invalid response format: missing or invalid 'topic' field")
                
                if "branches" not in result or not isinstance(result["branches"], list):
                    raise ValueError("Invalid response format: missing or invalid 'branches' array")
                
                # Validate each branch
                for branch in result["branches"]:
                    if not isinstance(branch, dict):
                        raise ValueError("Invalid branch format: must be an object")
                    
                    if "name" not in branch or not isinstance(branch["name"], str):
                        raise ValueError("Invalid branch format: missing or invalid 'name' field")
                    
                    if "subtopics" not in branch or not isinstance(branch["subtopics"], list):
                        raise ValueError("Invalid branch format: missing or invalid 'subtopics' array")
                    
                    # Validate each subtopic
                    for subtopic in branch["subtopics"]:
                        if not isinstance(subtopic, dict):
                            raise ValueError("Invalid subtopic format: must be an object")
                        
                        if "name" not in subtopic or not isinstance(subtopic["name"], str):
                            raise ValueError("Invalid subtopic format: missing or invalid 'name' field")
                        
                        if "details" not in subtopic or not isinstance(subtopic["details"], list):
                            raise ValueError("Invalid subtopic format: missing or invalid 'details' array")
                
                return {
                    "success": True,
                    "data": result
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {response_text}")
                raise ValueError(f"Invalid JSON format in AI response: {str(e)}")
            
        except ValueError as e:
            logger.error(f"Validation error in create_mindmap: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error creating mind map: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def simplify_topic(self, topic: str, complexity_level: str = "basic") -> Dict[str, Any]:
        """Simplify complex topics using ELI5 (Explain Like I'm 5) approach."""
        try:
            if not self.model:
                raise ValueError("AI model not initialized. Check if GEMINI_API_KEY is set correctly.")

            if not topic or not topic.strip():
                raise ValueError("Topic cannot be empty")

            complexity_prompts = {
                "basic": "like you're explaining to a 10-year-old, using very simple terms",
                "intermediate": "for a high school student, balancing simplicity with some technical details",
                "advanced": "for a college student, maintaining clarity while including technical concepts"
            }

            prompt = f"""
            Explain this topic {complexity_prompts.get(complexity_level, complexity_prompts["basic"])}.
            Break down complex concepts into simpler parts.
            Use clear analogies and real-world examples.
            
            Topic to explain: {topic}
            
            Respond with only a JSON object in this exact format:
            {{
                "original_topic": "{topic}",
                "simple_explanation": "A clear, simple explanation of the topic",
                "key_concepts": [
                    "Key concept 1 in simple terms",
                    "Key concept 2 in simple terms"
                ],
                "examples": [
                    "A concrete, real-world example 1",
                    "A concrete, real-world example 2"
                ],
                "analogies": [
                    "A relatable analogy 1",
                    "A relatable analogy 2"
                ]
            }}

            Requirements:
            1. No markdown formatting
            2. No code blocks
            3. Each array should have 2-4 items
            4. Keep explanations concise and clear
            5. Use language appropriate for the {complexity_level} level
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            try:
                # Handle possible markdown code blocks in response
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]  # Remove ```json and ``` markers
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]  # Remove ``` markers
                
                response_text = response_text.strip()
                result = json.loads(response_text)
                
                # Validate required fields and structure
                required_fields = ["original_topic", "simple_explanation", "key_concepts", "examples", "analogies"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field: {field}")
                    
                    # Check if arrays have the right type and structure
                    if field in ["key_concepts", "examples", "analogies"]:
                        if not isinstance(result[field], list):
                            raise ValueError(f"Field {field} must be an array")
                        if not result[field] or len(result[field]) < 1:
                            raise ValueError(f"Field {field} must have at least one item")
                        if not all(isinstance(item, str) for item in result[field]):
                            raise ValueError(f"All items in {field} must be strings")
                    
                    # Check string fields
                    if field in ["original_topic", "simple_explanation"]:
                        if not isinstance(result[field], str) or not result[field].strip():
                            raise ValueError(f"Field {field} must be a non-empty string")
                
                return {
                    "success": True,
                    "data": result
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {response_text}")
                raise ValueError(f"Invalid JSON format in AI response: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Validation error in simplify_topic: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error simplifying topic: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def extract_key_points(self, text: str) -> Dict[str, Any]:
        """Extract key points and important information from text."""
        try:
            if not text or not text.strip():
                raise ValueError("Input text cannot be empty")

            prompt = f"""
            Extract the key points, important facts, and main ideas from the following text.
            Organize them in a structured format.
            
            Text:
            {text}
            
            Please provide the key points in the following JSON format:
            {{
                "key_points": ["point 1", "point 2", "point 3"],
                "important_facts": ["fact 1", "fact 2"],
                "main_ideas": ["idea 1", "idea 2"],
                "vocabulary": ["term 1: definition", "term 2: definition"]
            }}
            
            Respond only with the JSON, no additional text.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            try:
                # Handle possible markdown code blocks in response
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]
                
                response_text = response_text.strip()
                result = json.loads(response_text)
                
                # Validate required fields
                required_fields = ["key_points", "important_facts", "main_ideas", "vocabulary"]
                if not all(key in result for key in required_fields):
                    missing_fields = [key for key in required_fields if key not in result]
                    raise ValueError(f"Missing required fields in AI response: {', '.join(missing_fields)}")
                
                # Ensure all fields are lists
                for field in required_fields:
                    if not isinstance(result[field], list):
                        result[field] = [str(result[field])]
                
                return {
                    "success": True,
                    "data": result
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {response_text}")
                raise ValueError(f"Invalid JSON format in AI response: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing AI response: {response_text}")
                raise ValueError(f"Error processing AI response: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Validation error in extract_key_points: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Create a singleton instance
ai_service = AIService()