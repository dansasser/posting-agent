import threading
import random
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.configs import settings
from app.telemetry.logger import get_logger
from app.telemetry import metrics
from app.adapters.facebook_client import FacebookClient
from app.agent.llm_client import LLMClient
from app.agent.generators import ContentGenerator
from app.agent import cards_loader
from app.agent.protocol_enforcer import ProtocolEnforcer
from app.safety.moderation import Moderator
from app.orchestrator import post_cycle
from app.orchestrator.engagement import EngagementManager
from app.database.engine import SessionLocal
from app.database.models import Post

# --- Global State ---
logger = get_logger(__name__)

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

@metrics.JOB_DURATION.time()
def scheduled_post_job():
    """
    The main job executed by the scheduler.
    It selects a random topic and post type, then runs the corresponding cycle
    and saves the new post to the database.
    """
    logger.info("Scheduler triggered. Starting a new post job.")

    db = SessionLocal()
    try:
        topic = random.choice(POST_TOPICS)
        post_type = random.choice(["thread", "longform"])
        new_post_id = None

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
            # Increment the posts created metric
            metrics.POSTS_CREATED.labels(post_type=post_type).inc()

            # Save the new post to the database
            new_post_record = Post(
                facebook_post_id=new_post_id,
                topic=topic,
                post_type=post_type,
                is_active_for_engagement=True
            )
            db.add(new_post_record)
            db.commit()
            logger.info(
                f"New post {new_post_id} saved to database and is being tracked for engagement."
            )

    except Exception as e:
        logger.error(f"An error occurred in the scheduled post job: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

def start_engagement_loop():
    """
    Starts the engagement monitoring loop in a background thread.
    """
    logger.info("Starting the engagement monitoring loop in a background thread.")
    engagement_thread = threading.Thread(
        target=engagement_manager.run_engagement_loop,
        daemon=True
    )
    engagement_thread.start()

def start_metrics_server_in_thread():
    """
    Starts the Prometheus metrics server in a background thread.
    """
    logger.info("Starting the metrics server in a background thread on port 8000.")
    metrics_thread = threading.Thread(
        target=metrics.start_metrics_server,
        args=(8000,),
        daemon=True
    )
    metrics_thread.start()


# --- Main Application Execution ---

def main():
    """
    Main function to set up the scheduler and start the application.
    """
    logger.info("--- Facebook Automation Agent Starting Up ---")

    # Start background services
    start_engagement_loop()
    start_metrics_server_in_thread()

    # Configure the scheduler
    scheduler = BlockingScheduler(timezone="UTC")

    trigger = CronTrigger(
        hour=",".join(map(str, settings.POST_SCHEDULE_HOURS)),
        minute=0,
        second=0
    )

    scheduler.add_job(
        scheduled_post_job,
        trigger=trigger,
        name="Scheduled Post Job",
    )

    logger.info(f"Scheduler configured to run at: {settings.POST_SCHEDULE_HOURS} UTC.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("--- Facebook Automation Agent Shutting Down ---")
        scheduler.shutdown()

if __name__ == "__main__":
    main()