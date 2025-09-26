import schedule
import time
import random
import threading
from typing import List, Dict, Any

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.configs import settings
from app.telemetry.logger import get_logger
from app.adapters.facebook_client import FacebookClient
from app.agent.llm_client import LLMClient
from app.agent.generators import ContentGenerator
from app.agent import cards_loader
from app.agent.protocol_enforcer import ProtocolEnforcer
from app.safety.moderation import Moderator
from app.orchestrator import post_cycle
from app.orchestrator.engagement import EngagementManager

# --- Global State ---
logger = get_logger(__name__)
# A simple, in-memory list of post IDs to monitor for engagement.
# In a larger application, this would be a database.
tracked_post_ids: List[str] = []
# A lock to safely append to the tracked_post_ids list from different threads.
thread_lock = threading.Lock()

# A predefined list of topics. This can be expanded or sourced from a file/API.
POST_TOPICS = [
    "The future of artificial intelligence in daily life.",
    "Tips for improving productivity while working from home.",
    "The importance of cybersecurity in a connected world.",
    "Exploring the benefits of a balanced diet and exercise.",
    "The impact of social media on modern communication.",
    "Creative ways to learn a new skill online.",
    "The role of renewable energy in combating climate change.",
]

# --- Initialization ---
try:
    # Load protocol once
    protocol_card = cards_loader.load_protocol("protocol_card.yaml")
    protocol_enforcer = ProtocolEnforcer(protocol_card)
    moderator = Moderator(protocol_card)

    # Initialize clients
    fb_client = FacebookClient()
    llm_client = LLMClient()

    # Initialize content generator
    content_generator = ContentGenerator(llm_client)

    # Initialize engagement manager
    engagement_manager = EngagementManager(fb_client, moderator, protocol_enforcer)

except (ValueError, FileNotFoundError) as e:
    logger.error(f"Initialization failed: {e}", exc_info=True)
    exit(1)

# --- Core Job Functions ---

def scheduled_post_job():
    """
    The main job executed by the scheduler.
    It selects a random topic and post type, then runs the corresponding cycle.
    """
    logger.info("Scheduler triggered. Starting a new post job.")

    try:
        topic = random.choice(POST_TOPICS)
        post_type = random.choice(["thread", "longform"])

        if post_type == "thread":
            recipe = cards_loader.load_recipe("recipe_thread_post.yaml")
            new_post_id = post_cycle.run_thread_cycle(
                topic, content_generator, fb_client, protocol_enforcer, recipe
            )
        else: # longform
            recipe = cards_loader.load_recipe("recipe_longform_post.yaml")
            new_post_id = post_cycle.run_longform_cycle(
                topic, content_generator, fb_client, protocol_enforcer, recipe
            )

        if new_post_id:
            with thread_lock:
                tracked_post_ids.append(new_post_id)
            logger.info(f"New post {new_post_id} is now being tracked for engagement.")

    except Exception as e:
        logger.error(f"An error occurred in the scheduled post job: {e}", exc_info=True)

def start_engagement_loop():
    """
    Starts the engagement monitoring loop in a background thread.
    """
    logger.info("Starting the engagement monitoring loop in a background thread.")
    # The engagement loop runs indefinitely, so it's started in a daemon thread.
    # This allows the main thread (scheduler) to exit gracefully.
    engagement_thread = threading.Thread(
        target=engagement_manager.run_engagement_loop,
        args=(tracked_post_ids,),
        daemon=True
    )
    engagement_thread.start()


# --- Main Application Execution ---

def main():
    """
    Main function to set up the scheduler and start the application.
    """
    logger.info("--- Facebook Automation Agent Starting Up ---")

    # Start the engagement loop in the background
    start_engagement_loop()

    # Configure the scheduler
    scheduler = BlockingScheduler(timezone="UTC")

    # Schedule the posting job based on hours defined in settings
    # Example: POST_SCHEDULE_HOURS = [9, 12, 15, 18, 21]
    trigger = CronTrigger(
        hour=",".join(map(str, settings.POST_SCHEDULE_HOURS)),
        minute=0, # Run at the top of the hour
        second=0
    )

    scheduler.add_job(
        scheduled_post_job,
        trigger=trigger,
        name="Scheduled Post Job",
    )

    logger.info(f"Scheduler configured to run at: {settings.POST_SCHEDULE_HOURS} UTC.")

    try:
        # For immediate testing, you can run a job right at the start
        # scheduled_post_job()

        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("--- Facebook Automation Agent Shutting Down ---")
        scheduler.shutdown()

if __name__ == "__main__":
    main()