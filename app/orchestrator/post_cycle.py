import time
import random
from typing import Dict, Any

from app.agent.generators import ContentGenerator
from app.agent.protocol_enforcer import ProtocolEnforcer
from app.adapters.facebook_client import FacebookClient
from app.telemetry.logger import get_logger

logger = get_logger(__name__)

def run_thread_cycle(
    topic: str,
    generator: ContentGenerator,
    fb_client: FacebookClient,
    protocol_enforcer: ProtocolEnforcer,
    recipe: Dict[str, Any],
) -> str | None:
    """
    Executes a full "Thread Post" cycle.

    This involves generating a main post, publishing it, and then publishing
    a series of threaded comments with delays.

    Args:
        topic: The topic for the content generation.
        generator: The content generator instance.
        fb_client: The Facebook client for API interactions.
        protocol_enforcer: The enforcer for content validation.
        recipe: The recipe card for the thread post style.

    Returns:
        The ID of the new post if successful, otherwise None.
    """
    logger.info(f"Starting thread post cycle for topic: '{topic}'")

    # 1. Generate the main post
    main_post_content = generator.generate_post(topic, recipe)
    if not main_post_content or not protocol_enforcer.validate_content(main_post_content):
        logger.error("Failed to generate or validate the main post. Aborting cycle.")
        return None

    # 2. Publish the main post
    post_id = fb_client.post_to_feed(main_post_content)
    if not post_id:
        logger.error("Failed to publish the main post to Facebook. Aborting cycle.")
        return None

    # 3. Generate comments
    comments_style = recipe.get("comments_style", {})
    comments = generator.generate_thread_comments(topic, main_post_content, recipe)
    if not comments:
        logger.warning("No comments were generated for the thread. Cycle ends.")
        return post_id

    # 4. Publish comments with staggered delays
    min_delay, max_delay = comments_style.get("stagger_seconds", [60, 180])
    last_comment_id = post_id  # First comment replies to the post

    for i, comment_text in enumerate(comments):
        if not protocol_enforcer.validate_content(comment_text):
            logger.warning(f"Comment {i+1} failed validation. Skipping.")
            continue

        # Stagger the comment posting
        delay = random.randint(min_delay, max_delay)
        logger.info(f"Waiting for {delay} seconds before posting comment {i+1}/{len(comments)}.")
        time.sleep(delay)

        new_comment_id = fb_client.add_comment(last_comment_id, comment_text)
        if new_comment_id:
            logger.info(f"Successfully posted comment {i+1}.")
            # Subsequent comments will reply to the previous comment to form a thread
            # Note: Facebook typically threads comments under the main post regardless,
            # but this could be useful for other platforms. We'll reply to the main post.
            # last_comment_id = new_comment_id
        else:
            logger.error(f"Failed to post comment {i+1}. Aborting remaining comments.")
            break

    logger.info(f"Thread post cycle for topic '{topic}' completed.")
    return post_id


def run_longform_cycle(
    topic: str,
    generator: ContentGenerator,
    fb_client: FacebookClient,
    protocol_enforcer: ProtocolEnforcer,
    recipe: Dict[str, Any],
) -> str | None:
    """
    Executes a "Longform Punchy Post" cycle.

    Args:
        topic: The topic for the content generation.
        generator: The content generator instance.
        fb_client: The Facebook client for API interactions.
        protocol_enforcer: The enforcer for content validation.
        recipe: The recipe card for the longform post style.

    Returns:
        The ID of the new post if successful, otherwise None.
    """
    logger.info(f"Starting longform post cycle for topic: '{topic}'")

    # 1. Generate the post
    post_content = generator.generate_post(topic, recipe)
    if not post_content or not protocol_enforcer.validate_content(post_content):
        logger.error("Failed to generate or validate the longform post. Aborting cycle.")
        return None

    # 2. Publish the post
    post_id = fb_client.post_to_feed(post_content)
    if post_id:
        logger.info(f"Longform post cycle for topic '{topic}' completed successfully.")
        return post_id
    else:
        logger.error("Failed to publish the longform post to Facebook.")
        return None