from typing import List, Optional, Dict, Any

from .llm_client import LLMClient
from . import prompt_templates
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class ContentGenerator:
    """
    Generates content for Facebook posts and comments using an LLM.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initializes the content generator.

        Args:
            llm_client: An instance of the LLM client.
        """
        self.llm_client = llm_client

    def generate_post(self, topic: str, recipe: Dict[str, Any]) -> Optional[str]:
        """
        Generates a main post based on a topic and a recipe.

        Args:
            topic: The topic of the post.
            recipe: The recipe dictionary defining the style.

        Returns:
            The generated post content as a string, or None on failure.
        """
        style_guide = recipe.get("post_style", {})
        prompt = prompt_templates.create_post_prompt(topic, style_guide)
        system_prompt = prompt_templates.COPYWRITER_SYSTEM_PROMPT

        logger.info(f"Generating main post for topic: '{topic}'")
        content = self.llm_client.generate_text(prompt, system_prompt=system_prompt)
        return content

    def generate_thread_comments(
        self, topic: str, main_post_content: str, recipe: Dict[str, Any]
    ) -> List[str]:
        """
        Generates a series of comments for a thread post.

        Args:
            topic: The topic of the thread.
            main_post_content: The content of the initial post.
            recipe: The recipe dictionary defining the style.

        Returns:
            A list of generated comment strings.
        """
        comments_style = recipe.get("comments_style", {})
        num_comments = comments_style.get("count", 5)
        generated_comments = []

        logger.info(f"Generating {num_comments} comments for topic: '{topic}'")
        for i in range(1, num_comments + 1):
            prompt = prompt_templates.create_thread_comment_prompt(
                topic=topic,
                main_post_content=main_post_content,
                comment_index=i,
                total_comments=num_comments,
                style_guide=comments_style,
            )
            system_prompt = prompt_templates.COPYWRITER_SYSTEM_PROMPT

            logger.info(f"Generating comment {i}/{num_comments}...")
            comment = self.llm_client.generate_text(prompt, system_prompt=system_prompt)

            if comment:
                generated_comments.append(comment)
                logger.info(f"Successfully generated comment {i}/{num_comments}.")
            else:
                logger.warning(f"Failed to generate comment {i}/{num_comments}. Stopping generation for this thread.")
                break  # Stop if one comment fails

        return generated_comments