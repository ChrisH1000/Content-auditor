"""Tone analysis chain using LangChain and Ollama."""

import json
import logging
import os
from typing import Optional

from langchain_community.llms import Ollama
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToneAnalysisOutput(BaseModel):
    """Structured output for tone analysis."""
    readability: str = Field(description="Brief readability assessment (max 2 sentences)")
    tone: str = Field(description="Brief tone description (max 2 sentences)")
    risks: str = Field(description="Potential risks or issues (max 2 sentences)")


def analyze_tone(
    text: str,
    model_name: str = None,
    base_url: str = None,
    max_length: int = 1200
) -> Optional[dict]:
    """
    Analyze tone and readability of text using LLM.
    
    Args:
        text: Text content to analyze
        model_name: Ollama model name (defaults to env var)
        base_url: Ollama base URL (defaults to env var)
        max_length: Maximum text length to analyze
        
    Returns:
        Dictionary with readability, tone, and risks, or None on error
    """
    try:
        # Get configuration from environment
        if model_name is None:
            model_name = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Truncate text if needed
        if len(text) > max_length:
            text = text[:max_length]
            logger.debug(f"Text truncated to {max_length} characters for LLM analysis")
        
        # Initialize Ollama LLM
        llm = Ollama(
            model=model_name,
            base_url=base_url,
            temperature=0.3,
        )
        
        # Construct prompt
        prompt = f"""You are a concise content analyzer. Analyze the following text for tone and readability.

Provide your response as a JSON object with these exact keys:
- "readability": Brief assessment (max 2 sentences)
- "tone": Brief description (max 2 sentences)
- "risks": Potential issues (max 2 sentences)

Text to analyze:
{text}

Response (JSON only):"""
        
        # Call LLM
        logger.debug(f"Calling Ollama model: {model_name}")
        response = llm.invoke(prompt)
        
        # Parse response
        try:
            # Try to extract JSON from response
            response = response.strip()
            
            # Handle markdown code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
                response = response.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(response)
            
            # Validate keys
            required_keys = ["readability", "tone", "risks"]
            if not all(key in result for key in required_keys):
                logger.error(f"LLM response missing required keys: {result}")
                return {
                    "readability": "Unable to analyze",
                    "tone": "Unable to analyze",
                    "risks": "Analysis failed - invalid response format"
                }
            
            logger.debug("Tone analysis completed successfully")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            return {
                "readability": "Unable to analyze",
                "tone": "Unable to analyze",
                "risks": f"Analysis failed - JSON parse error"
            }
    
    except Exception as e:
        logger.error(f"Error in tone analysis: {e}")
        return None
