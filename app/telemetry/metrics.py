from prometheus_client import Counter, Summary, start_http_server

# --- Metric Definitions ---

# A counter to track the total number of posts created.
# The 'post_type' label will differentiate between 'thread' and 'longform'.
POSTS_CREATED = Counter(
    "facebook_agent_posts_created_total",
    "Total number of posts created by the agent",
    ["post_type"]
)

# A counter to track the total number of API errors encountered.
# The 'client' label will differentiate between 'facebook' and 'openai'.
API_ERRORS = Counter(
    "facebook_agent_api_errors_total",
    "Total number of API errors encountered",
    ["client"]
)

# A summary to track the duration of scheduled post jobs.
# This will provide metrics like the count and sum of job durations.
JOB_DURATION = Summary(
    "facebook_agent_job_duration_seconds",
    "Duration of scheduled post jobs in seconds"
)

# --- Metrics Server ---

def start_metrics_server(port: int = 8000):
    """
    Starts an HTTP server to expose the defined metrics.
    This should be run in a separate thread from the main application logic.

    Args:
        port: The port on which to expose the metrics.
    """
    start_http_server(port)