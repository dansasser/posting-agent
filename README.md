# Facebook Automation Agent

This project is a general-purpose Facebook automation agent designed to schedule and publish content to a Facebook page. It supports different posting strategies, including "Thread Posts" (a short post followed by threaded comments) and "Longform Posts". The agent is built with a modular architecture that is easy to extend.

## Features

- **Two Post Modes:**
  - **Thread Post:** A short initial post with a series of follow-up comments.
  - **Longform Punchy Post:** A single, well-structured post of 150-250 words.
- **Scheduled Posting:** Uses APScheduler to publish content at configurable times.
- **Content Generation:** Leverages an LLM (e.g., OpenAI's GPT models) to generate high-quality, on-topic content.
- **Style and Safety:**
  - **Recipes (YAML):** Define the style, tone, and structure of generated content.
  - **Protocols (YAML):** Enforce universal safety rules, content constraints, and engagement policies.
- **Engagement Monitoring:** A basic framework for monitoring comments on published posts.
- **Dockerized:** Comes with a `Dockerfile` and `docker-compose.yml` for easy and consistent deployment.
- **Structured Logging:** Outputs JSON logs for better observability.

## Repository Structure

```
app/
  orchestrator/   # Core logic for posting and engagement cycles
  agent/          # LLM client, prompt templates, and content generators
  adapters/       # Client for interacting with the Facebook Graph API
  recipes/        # YAML files defining content styles
  protocols/      # YAML files defining content rules
  safety/         # Moderation and rate-limiting logic
  configs/        # Configuration management
  telemetry/      # Structured logging
  main.py         # Main application entrypoint with scheduler
Dockerfile
docker-compose.yml
.env.example
README.md
```

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose**
- A **Facebook Page** you manage.
- A **Meta Developer Account** with an app that has the necessary permissions (`pages_manage_posts`, `pages_read_engagement`).
- An **OpenAI API Key**.

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a `.env` file:**
    Copy the example environment file and fill in your credentials.
    ```bash
    cp .env.example .env
    ```

3.  **Edit the `.env` file** with your specific credentials:
    - `FACEBOOK_APP_ID`: Your Meta App ID.
    - `FACEBOOK_APP_SECRET`: Your Meta App Secret.
    - `FACEBOOK_PAGE_ID`: The ID of the Facebook Page you want to post to.
    - `FACEBOOK_USER_ACCESS_TOKEN`: A User Access Token with the required permissions. You can generate this from the Meta for Developers portal.
    - `OPENAI_API_KEY`: Your API key from OpenAI.
    - `POST_SCHEDULE_HOURS`: A comma-separated list of hours (0-23, UTC) to schedule posts (e.g., `9,12,15,18,21`).

### Running the Agent

The application is designed to be run with Docker Compose, which handles building the image and running the container with the correct environment variables.

1.  **Build and run the container:**
    ```bash
    docker-compose up --build
    ```

2.  **Run in detached mode** (in the background):
    ```bash
    docker-compose up --build -d
    ```

The agent will now be running. It will automatically trigger posting jobs at the hours specified in your `.env` file.

### Viewing Logs

You can view the structured logs from the running container:
```bash
docker-compose logs -f
```

## How It Works

1.  **Scheduler (`main.py`):** The `BlockingScheduler` from `APScheduler` is the heart of the application. It triggers a `scheduled_post_job` at the times defined by `POST_SCHEDULE_HOURS`.
2.  **Job Execution:** When a job runs, it randomly selects a topic and a post type ("thread" or "longform").
3.  **Recipe & Protocol Loading:** It loads the corresponding YAML `recipe` for style and the master `protocol` for safety rules.
4.  **Content Generation (`agent/`):** The `ContentGenerator` uses the `LLMClient` and `prompt_templates` to create content that matches the topic and recipe guidelines.
5.  **Validation (`protocol_enforcer.py`):** The generated content is validated against the rules in the protocol card to ensure it's safe and meets length/format requirements.
6.  **Posting (`adapters/facebook_client.py`):** The `FacebookClient` posts the validated content to your page via the Facebook Graph API.
7.  **Engagement (`orchestrator/engagement.py`):** A background thread monitors the posts made by the agent, checking for new comments and applying engagement rules (e.g., rate-limiting).

## Extensibility

-   **Add New Topics:** Add more strings to the `POST_TOPICS` list in `app/main.py`.
-   **Create New Recipes:** Add new `recipe_*.yaml` files in `app/recipes/` and update the logic in `scheduled_post_job` to use them.
-   **Modify Protocols:** Adjust the rules in `app/protocols/protocol_card.yaml` to change safety constraints or engagement policies.
-   **Enhance Engagement:** The `EngagementManager` in `app/orchestrator/engagement.py` can be extended with more sophisticated logic to generate AI-powered replies to user comments.