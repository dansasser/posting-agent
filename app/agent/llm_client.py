import openai
from typing import Optional

from app.configs import settings
from app.telemetry.logger import get_logger
from app.telemetry import metrics

logger = get_logger(__name__)

class LLMClient:
    """
    A client for interacting with a Large Language Model (LLM) API, like OpenAI.
    """

    def __init__(self, api_key: str = settings.OPENAI_API_KEY):
        """
        Initializes the LLM client.

        Args:
            api_key: The API key for the LLM service.
        """
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set.")
        self.client = openai.OpenAI(api_key=api_key)

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """
        Generates text using the specified LLM.

        Args:
            prompt: The main user prompt for the generation.
            system_prompt: An optional system-level prompt to guide the model's behavior.
            model: The model to use for generation.
            max_tokens: The maximum number of tokens to generate.
            temperature: The creativity of the generation (0.0 to 2.0).

        Returns:
            The generated text as a string, or None if generation fails.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.info(f"Generating text with model {model} and prompt: '{prompt[:100]}...'")
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            logger.info(f"Successfully generated text. Length: {len(content)} chars.")
            return content.strip() if content else None
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            metrics.API_ERRORS.labels(client='openai').inc()
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during text generation: {e}")
            metrics.API_ERRORS.labels(client='openai').inc()
            return None