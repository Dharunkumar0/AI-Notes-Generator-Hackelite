import httpx
import json
import logging
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        try:
            # Configure Ollama API endpoint
            logger.debug("Initializing Ollama API...")
            self.api_base = "http://localhost:11434"  # Default Ollama API endpoint
            self.model_name = "mistral"  # You can change this to any model you have pulled in Ollama
            
            # Configure timeouts and limits
            self.timeout = httpx.Timeout(
                connect=5.0,    # connection timeout
                read=300.0,    # read timeout (5 minutes)
                write=60.0,    # write timeout
                pool=60.0      # pool timeout
            )
            
            # Test connection
            with httpx.Client(timeout=self.timeout) as client:
                try:
                    response = client.get(f"{self.api_base}/api/tags")
                    if response.status_code == 200:
                        logger.debug("Ollama API connection successful")
                    else:
                        raise Exception(f"Failed to connect to Ollama API: {response.status_code}")
                except httpx.TimeoutError:
                    raise Exception("Timeout while connecting to Ollama API. Make sure Ollama is running.")
                except httpx.ConnectError:
                    raise Exception("Could not connect to Ollama API. Make sure Ollama is running on localhost:11434")
                
        except Exception as e:
            logger.error(f"Error initializing AI Service: {str(e)}")
            raise

    async def summarize_notes(
        self, 
        text: str, 
        max_length: int = 500,
        summarization_type: str = 'abstractive',
        summary_mode: str = 'narrative',
        use_blooms_taxonomy: bool = False
    ) -> Dict[str, Any]:
        """
        Summarize text using AI with specified summarization type and style.
        
        Args:
            text: The input text to summarize
            max_length: Maximum length of the summary in words
            summarization_type: 'abstractive' or 'extractive'
            summary_mode: 'narrative', 'beginner', 'technical', or 'bullet'
        """
        try:
            # Define style instructions for each mode
            style_instructions = {
                'narrative': "Write the summary in a flowing, story-like manner that's engaging and easy to follow.",
                'beginner': "Use simple, clear language suitable for beginners. Avoid technical terms and explain concepts in basic terms.",
                'technical': "Use precise technical language and domain-specific terminology. Maintain a professional and academic tone.",
                'bullet': "Present the summary as a structured list of key points, using bullet points for clarity."
            }.get(summary_mode, "Write in a clear, concise manner.")

            # Define method instructions for summarization type
            method_instructions = {
                'extractive': "Create the summary by selecting and combining the most important sentences from the original text. Maintain the original wording where possible.",
                'abstractive': "Generate a new summary that captures the meaning of the text in your own words. Rephrase and restructure the content while maintaining accuracy."
            }.get(summarization_type, "Summarize the text appropriately.")

            # Add Bloom's Taxonomy instructions if requested
            blooms_instructions = """ 
            Additionally, analyze the content using Bloom's Taxonomy and provide learning objectives at each level:
            {
                "blooms_taxonomy": {
                    "remember": ["Learning objectives focusing on recall of facts, terms, basic concepts"],
                    "understand": ["Learning objectives focusing on comprehending meaning"],
                    "apply": ["Learning objectives focusing on using information in new situations"],
                    "analyze": ["Learning objectives focusing on drawing connections"],
                    "evaluate": ["Learning objectives focusing on justifying positions"],
                    "create": ["Learning objectives focusing on creating new or original work"]
                }
            }
            """ if use_blooms_taxonomy else ""

            # Add format-specific instructions
            format_instructions = f"""
            Present the summary in the following JSON format:
            {{
                "summary": "the summarized text",
                "key_points": ["point 1", "point 2", "point 3"],
                "word_count": number_of_words_in_summary
                {"," if use_blooms_taxonomy else ""}
                {"\"blooms_taxonomy\": {...}" if use_blooms_taxonomy else ""}
            }}
            """

            prompt = f"""
            Please summarize the following text according to these specifications:
            
            Style: {style_instructions}
            Method: {method_instructions}
            Maximum Length: {max_length} words
            
            Text to summarize:
            {text}
            
            {format_instructions}
            
            Respond only with the JSON, no additional text.
            """
            
            # Make request to Ollama API
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.api_base}/api/generate",
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9,
                                "num_predict": 2048,  # Adjust based on your needs
                                "stop": ["```"]  # Stop at code blocks
                            }
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                        return {
                            "success": False,
                            "error": f"Ollama API error: {response.status_code}"
                        }

                    response_data = response.json()
                    if not response_data:
                        return {
                            "success": False,
                            "error": "Empty response from Ollama API"
                        }

                    response_text = response_data.get('response', '')
                    if not response_text:
                        return {
                            "success": False,
                            "error": "No response text from Ollama API"
                        }

                    # Try to parse the response as JSON
                    try:
                        if response_text.startswith('```json'):
                            response_text = response_text[7:-3]  # Remove ```json and ``` markers
                        elif response_text.startswith('```'):
                            response_text = response_text[3:-3]  # Remove ``` markers
                        
                        response_text = response_text.strip()
                        summary_data = json.loads(response_text)
                        
                        # Validate the required fields
                        if not all(key in summary_data for key in ["summary", "key_points", "word_count"]):
                            # Create a structured response if the model didn't provide the exact format
                            summary_data = {
                                "summary": summary_data.get("summary", response_text),
                                "key_points": summary_data.get("key_points", []),
                                "word_count": summary_data.get("word_count", len(response_text.split()))
                            }
                        
                        return {
                            "success": True,
                            "data": summary_data
                        }
                    except json.JSONDecodeError:
                        # If we can't parse JSON, return the text as a summary
                        return {
                            "success": True,
                            "data": {
                                "summary": response_text,
                                "key_points": [],
                                "word_count": len(response_text.split())
                            }
                        }
                        
            except httpx.ReadTimeout as e:
                logger.error(f"Timeout while calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Request timed out. The model is taking too long to respond."
                }
            except httpx.ConnectTimeout as e:
                logger.error(f"Connection timeout with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Connection timed out."
                }
            except httpx.ConnectError as e:
                logger.error(f"Connection error with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Make sure the service is running."
                }
            except Exception as e:
                logger.error(f"Error calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": f"Failed to generate summary: {str(e)}"
                }
                
                try:
                    result = response.json()
                    response_text = result.get('response', '').strip()
                    
                    # Handle possible markdown code block formatting
                    if response_text.startswith('```json'):
                        response_text = response_text[7:-3]  # Remove ```json and ``` markers
                    elif response_text.startswith('```'):
                        response_text = response_text[3:-3]  # Remove ``` markers
                    
                    response_text = response_text.strip()
                    
                    # Parse the JSON response from the model
                    try:
                        summary_data = json.loads(response_text)
                        # Validate required fields
                        if not all(key in summary_data for key in ["summary", "key_points", "word_count"]):
                            raise ValueError("Missing required fields in AI response")
                            
                        return {
                            "success": True,
                            "data": summary_data
                        }
                    except json.JSONDecodeError:
                        # If the model didn't return proper JSON, create a basic structure
                        summary_data = {
                            "summary": response_text,
                            "key_points": [],
                            "word_count": len(response_text.split())
                        }
                        return {
                            "success": True,
                            "data": summary_data
                        }
                except Exception as e:
                    logger.error(f"Error processing Ollama response: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e)
                    }
        except Exception as e:
            logger.error(f"Error summarizing notes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_quiz(self, text: str, num_questions: int = 5, use_blooms_taxonomy: bool = False, taxonomy_levels: List[str] = None) -> Dict[str, Any]:
        """Generate quiz questions from text using Ollama."""
        try:
            if not text or not text.strip():
                raise ValueError("Input text cannot be empty")

            # Split long text into chunks if needed
            max_chunk_size = 4000
            if len(text) > max_chunk_size:
                text = text[:max_chunk_size]  # Take first chunk for quiz generation
                logger.warning(f"Text truncated to {max_chunk_size} characters for quiz generation")

            taxonomy_instruction = ""
            if use_blooms_taxonomy:
                taxonomy_levels = taxonomy_levels or ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
                taxonomy_instruction = f"""
                Use Bloom's Taxonomy to create questions at different cognitive levels:
                - Remember: Test recall of specific facts and basic concepts
                - Understand: Test comprehension and ability to explain ideas
                - Apply: Test ability to use information in new situations
                - Analyze: Test ability to draw connections and find patterns
                - Evaluate: Test ability to justify a position or decision
                - Create: Test ability to create new or original work

                Distribute questions across these cognitive levels: {', '.join(taxonomy_levels)}
                Each question should clearly target one of these cognitive levels.
                """

            prompt = f"""
            You are a quiz generator. Based on the following text, generate {num_questions} multiple choice questions.

            Text to analyze:
            {text}

            {taxonomy_instruction}

            For each question:
            1. Generate a clear, specific question
            2. Create 4 distinct answer options labeled A, B, C, D
            3. Mark one option as correct
            4. Provide a brief explanation for why the correct answer is right
            5. {"Include the targeted cognitive level (e.g., 'Cognitive Level: Remember')" if use_blooms_taxonomy else ""}

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
            4. Questions should test understanding, not just memorization
            5. No markdown formatting or extra text
            6. Return only valid JSON matching the exact structure above

            Respond only with the JSON object, no additional text.
            """
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.api_base}/api/generate",
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9,
                                "num_predict": 2048
                            }
                        }
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Ollama API request failed: {response.text}")
                        
                    response_data = response.json()
                    response_text = response_data.get("response", "").strip()
                    
                    if not response_text:
                        raise ValueError("Empty response from Ollama")
                        
                    # Clean up response text
                    if response_text.startswith('```json'):
                        response_text = response_text[7:-3]
                    elif response_text.startswith('```'):
                        response_text = response_text[3:-3]
                    
                    response_text = response_text.strip()
                    
                    try:
                        result = json.loads(response_text)
                        
                        # Validate structure
                        if "questions" not in result or not isinstance(result["questions"], list):
                            raise ValueError("Invalid response format: missing or invalid 'questions' array")
                        
                        if len(result["questions"]) == 0:
                            raise ValueError("No questions generated")
                        
                        # Set total_questions
                        result["total_questions"] = len(result["questions"])
                        
                        # Validate and fix each question
                        for q in result["questions"]:
                            if not all(key in q for key in ["question", "options", "correct_answer", "explanation"]):
                                raise ValueError("Invalid question format: missing required fields")
                            
                            # Ensure options is a list of 4 items
                            if not isinstance(q["options"], list) or len(q["options"]) != 4:
                                raise ValueError("Invalid options format: must be an array of 4 items")
                            
                            # Fix option formatting
                            for i, option in enumerate(q["options"]):
                                expected_prefix = f"{chr(65 + i)}) "  # A), B), C), D)
                                if not option.startswith(expected_prefix):
                                    q["options"][i] = f"{expected_prefix}{option.lstrip('ABCD) ')}"
                            
                            # Fix correct_answer format
                            if not any(q["correct_answer"] == opt for opt in q["options"]):
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
                        
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse Ollama response as JSON: {response_text}")
                        raise ValueError("Invalid JSON format in response")
                    
            except httpx.ReadTimeout as e:
                logger.error(f"Timeout while calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Request timed out. The model is taking too long to respond."
                }
            except httpx.ConnectTimeout as e:
                logger.error(f"Connection timeout with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Connection timed out."
                }
            except httpx.ConnectError as e:
                logger.error(f"Connection error with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Make sure the service is running."
                }
            except Exception as e:
                logger.error(f"Error calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": f"Failed to generate quiz: {str(e)}"
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
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.api_base}/api/generate",
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9,
                                "num_predict": 2048
                            }
                        }
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Ollama API request failed: {response.text}")
                        
                    response_data = response.json()
                    response_text = response_data.get("response", "").strip()
                    
                    if not response_text:
                        raise ValueError("Empty response from Ollama")
                        
                    # Clean response
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
                    
            except httpx.ReadTimeout as e:
                logger.error(f"Timeout while calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Request timed out. The model is taking too long to respond."
                }
            except httpx.ConnectTimeout as e:
                logger.error(f"Connection timeout with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Connection timed out."
                }
            except httpx.ConnectError as e:
                logger.error(f"Connection error with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Make sure the service is running."
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response: {response_text}")
                return {
                    "success": False,
                    "error": f"Invalid JSON format in response: {str(e)}"
                }
            except Exception as e:
                logger.error(f"Error calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": f"Failed to process response: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Error creating mind map: {e}")
            return {
                "success": False,
                "error": str(e)
            }
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
            
            Return only the JSON object, no additional text.
            """
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.api_base}/api/generate",
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9,
                                "num_predict": 2048
                            }
                        }
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Ollama API request failed: {response.text}")
                        
                    response_data = response.json()
                    response_text = response_data.get("response", "").strip()
                    
                    if not response_text:
                        raise ValueError("Empty response from Ollama")
                    
                    # Clean response
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
                                
                    return {
                        "success": True,
                        "data": result
                    }
                    
            except httpx.ReadTimeout as e:
                logger.error(f"Timeout while calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Request timed out. The model is taking too long to respond."
                }
            except httpx.ConnectTimeout as e:
                logger.error(f"Connection timeout with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Connection timed out."
                }
            except httpx.ConnectError as e:
                logger.error(f"Connection error with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Make sure the service is running."
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response: {response_text}")
                return {
                    "success": False,
                    "error": f"Invalid JSON format in response: {str(e)}"
                }
            except Exception as e:
                logger.error(f"Error calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": f"Failed to process response: {str(e)}"
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
            You are a precise JSON generator. Extract key information from the following text and format it as JSON.
            
            Text to analyze:
            {text}
            
            Instructions:
            1. Extract key points, important facts, main ideas, and vocabulary
            2. Format response as VALID JSON only
            3. No explanation, markdown, or extra text
            4. Must match this exact structure:
            {{
                "key_points": ["point 1", "point 2", "point 3"],
                "important_facts": ["fact 1", "fact 2"],
                "main_ideas": ["idea 1", "idea 2"],
                "vocabulary": ["term 1: definition", "term 2: definition"]
            }}
            
            Rules:
            - Each array must contain at least 2 items
            - No nested objects, only string arrays
            - Each string should be a complete, meaningful phrase
            - No line breaks within the JSON strings
            - Use double quotes for JSON properties and strings
            - No comments or extra text before or after the JSON

            Return only valid JSON matching the exact structure above.
            """
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.api_base}/api/generate",
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9,
                                "num_predict": 2048
                            }
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                        return {
                            "success": False,
                            "error": f"Ollama API error: {response.status_code}"
                        }

                    response_data = response.json()
                    if not response_data:
                        return {
                            "success": False,
                            "error": "Empty response from Ollama API"
                        }

                    response_text = response_data.get('response', '')
                    if not response_text:
                        return {
                            "success": False,
                            "error": "No response text from Ollama API"
                        }

                    # Clean and parse the response
                    try:
                        # Remove any potential prefixes or suffixes
                        response_lines = response_text.split('\n')
                        json_lines = []
                        in_json = False
                        
                        for line in response_lines:
                            line = line.strip()
                            if line.startswith('{'):
                                in_json = True
                            if in_json:
                                json_lines.append(line)
                            if line.endswith('}'):
                                break
                        
                        if json_lines:
                            response_text = '\n'.join(json_lines)
                        
                        # Remove any markdown code blocks
                        if response_text.startswith('```json'):
                            response_text = response_text[7:]
                        if response_text.startswith('```'):
                            response_text = response_text[3:]
                        if response_text.endswith('```'):
                            response_text = response_text[:-3]
                            
                        response_text = response_text.strip()
                        result = json.loads(response_text)
                        
                        # Validate required fields
                        required_fields = ["key_points", "important_facts", "main_ideas", "vocabulary"]
                        
                        # Initialize missing fields with empty arrays
                        for field in required_fields:
                            if field not in result:
                                result[field] = []
                            elif not isinstance(result[field], list):
                                result[field] = [str(result[field])]
                        
                        # Ensure each field has at least one item
                        for field in required_fields:
                            if not result[field]:
                                result[field] = ["No " + field.replace('_', ' ') + " found"]
                        
                        return {
                            "success": True,
                            "data": result
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error: {str(e)}")
                        logger.error(f"Raw response: {response_text}")
                        
                        # Try to extract meaningful content even if JSON parsing fails
                        try:
                            # Create a basic structure from the text
                            lines = response_text.split('\n')
                            points = [line.strip() for line in lines if line.strip() and not line.strip().startswith('{') and not line.strip().endswith('}')]
                            
                            return {
                                "success": True,
                                "data": {
                                    "key_points": points[:3] if points else ["Could not extract key points"],
                                    "important_facts": points[3:5] if len(points) > 3 else ["No facts extracted"],
                                    "main_ideas": points[5:7] if len(points) > 5 else ["No main ideas extracted"],
                                    "vocabulary": points[7:9] if len(points) > 7 else ["No vocabulary extracted"]
                                }
                            }
                        except Exception as e2:
                            logger.error(f"Fallback parsing error: {str(e2)}")
                            return {
                                "success": False,
                                "error": "Could not parse model response"
                            }
                        
            except httpx.ReadTimeout as e:
                logger.error(f"Timeout while calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Request timed out. The model is taking too long to respond."
                }
            except httpx.ConnectTimeout as e:
                logger.error(f"Connection timeout with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Connection timed out."
                }
            except httpx.ConnectError as e:
                logger.error(f"Connection error with Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": "Could not connect to Ollama. Make sure the service is running."
                }
            except Exception as e:
                logger.error(f"Error calling Ollama API: {str(e)}")
                return {
                    "success": False,
                    "error": f"Failed to generate key points: {str(e)}"
                }
                
        except ValueError as e:
            logger.error(f"Validation error in extract_key_points: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def process_voice_to_notes(self, speech_text: str) -> Dict[str, Any]:
        """Process voice/speech text and convert to clean notes."""
        try:
            if not speech_text or not speech_text.strip():
                raise ValueError("Speech text cannot be empty")

            prompt = f"""
            Clean and process the following speech text, then create bullet-point notes from it.
            
            Speech text:
            {speech_text}
            
            Please provide the result in the following JSON format:
            {{
                "cleaned_text": "The cleaned and corrected version of the speech text",
                "notes": [
                    "First bullet point note",
                    "Second bullet point note",
                    "Third bullet point note"
                ]
            }}
            
            Requirements:
            1. Clean up any speech-to-text errors, filler words, and repetitions
            2. Make the cleaned text readable and grammatically correct
            3. Create 3-5 concise bullet-point notes from the content
            4. Keep notes factual and easy to read
            5. No markdown formatting in the response
            
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
                required_fields = ["cleaned_text", "notes"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field: {field}")
                    
                    if field == "cleaned_text":
                        if not isinstance(result[field], str) or not result[field].strip():
                            raise ValueError("cleaned_text must be a non-empty string")
                    elif field == "notes":
                        if not isinstance(result[field], list) or not result[field]:
                            raise ValueError("notes must be a non-empty array")
                        if not all(isinstance(item, str) for item in result[field]):
                            raise ValueError("All notes must be strings")
                
                return {
                    "success": True,
                    "data": result
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {response_text}")
                raise ValueError(f"Invalid JSON format in AI response: {str(e)}")
                
        except ValueError as e:
            logger.error(f"Validation error in process_voice_to_notes: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error processing voice to notes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Create a singleton instance
ai_service = AIService()