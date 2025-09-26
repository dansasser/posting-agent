import requests
from typing import Optional, Dict, Any

from app.configs import settings
from app.telemetry.logger import get_logger
from app.telemetry import metrics

logger = get_logger(__name__)

class FacebookClient:
    """
    A client for interacting with the Facebook Graph API.

    This client provides a clean, high-level interface for common Facebook
    actions like posting to a feed, adding comments, and fetching comments.
    It is designed to be swappable with other adapters (e.g., an MCP Tool Adapter)
    in the future.
    """
    API_VERSION = "v18.0"
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

    def __init__(
        self,
        page_id: str = settings.FACEBOOK_PAGE_ID,
        access_token: str = settings.FACEBOOK_USER_ACCESS_TOKEN,
    ):
        """
        Initializes the Facebook client.

        Args:
            page_id: The ID of the Facebook Page to interact with.
            access_token: A User Access Token with necessary permissions.
        """
        if not page_id or not access_token:
            raise ValueError("FACEBOOK_PAGE_ID and FACEBOOK_USER_ACCESS_TOKEN must be set.")
        self.page_id = page_id
        self.access_token = access_token
        self.session = requests.Session()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Helper method to make requests to the Graph API.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        if params is None:
            params = {}
        params["access_token"] = self.access_token

        try:
            response = self.session.request(method, url, params=params, json=json)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP Error for {method.upper()} {url}: {e.response.status_code} "
                f"Response: {e.response.text}"
            )
            metrics.API_ERRORS.labels(client='facebook').inc()
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {method.upper()} {url}: {e}")
            metrics.API_ERRORS.labels(client='facebook').inc()
            raise

    def post_to_feed(self, message: str) -> Optional[str]:
        """
        Posts a message to the Facebook page's feed.

        Args:
            message: The text content to post.

        Returns:
            The ID of the newly created post, or None if it fails.
        """
        endpoint = f"{self.page_id}/feed"
        payload = {"message": message}
        logger.info(f"Posting to feed for page {self.page_id}: '{message[:50]}...'")
        try:
            response = self._request("POST", endpoint, json=payload)
            post_id = response.get("id")
            if post_id:
                logger.info(f"Successfully posted to feed. Post ID: {post_id}")
                return post_id
            logger.warning("Post to feed did not return an ID.", extra={"response": response})
            return None
        except requests.exceptions.RequestException:
            return None

    def add_comment(self, object_id: str, message: str) -> Optional[str]:
        """
        Adds a comment to a Facebook object (post or comment).

        Args:
            object_id: The ID of the post or comment to reply to.
            message: The text content of the comment.

        Returns:
            The ID of the newly created comment, or None if it fails.
        """
        endpoint = f"{object_id}/comments"
        payload = {"message": message}
        logger.info(f"Adding comment to object {object_id}: '{message[:50]}...'")
        try:
            response = self._request("POST", endpoint, json=payload)
            comment_id = response.get("id")
            if comment_id:
                logger.info(f"Successfully added comment. Comment ID: {comment_id}")
                return comment_id
            logger.warning("Add comment did not return an ID.", extra={"response": response})
            return None
        except requests.exceptions.RequestException:
            return None

    def send_direct_message(self, user_id: str, message: str) -> Optional[str]:
        """
        Sends a direct message to a user via Facebook Messenger.

        Args:
            user_id: The Facebook ID of the recipient.
            message: The message body to send.

        Returns:
            The ID of the sent message if successful, otherwise None.
        """
        endpoint = f"{self.page_id}/messages"
        payload = {
            "recipient": {"id": user_id},
            "message": {"text": message},
            "messaging_type": "RESPONSE",
        }

        logger.info(
            "Sending direct message.",
            extra={"user_id": user_id, "preview": message[:50]},
        )

        try:
            response = self._request("POST", endpoint, json=payload)
            message_id = response.get("message_id")
            if message_id:
                logger.info(
                    "Successfully sent direct message.",
                    extra={"user_id": user_id, "message_id": message_id},
                )
                return message_id

            logger.warning(
                "Direct message response missing message_id.",
                extra={"user_id": user_id, "response": response},
            )
            return None
        except requests.exceptions.RequestException:
            return None

    def get_comments(self, post_id: str) -> Dict[str, Any]:
        """
        Retrieves comments from a specific post.

        Args:
            post_id: The ID of the post to fetch comments from.

        Returns:
            A dictionary containing the comment data from the API.
        """
        endpoint = f"{post_id}/comments"
        params = {"fields": "id,message,from,created_time"}
        logger.info(f"Fetching comments for post {post_id}")
        try:
            return self._request("GET", endpoint, params=params)
        except requests.exceptions.RequestException:
            return {"data": []}