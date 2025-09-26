import pytest
from unittest import mock

from app.orchestrator import post_cycle

# A sample recipe for a longform post
LONGFORM_RECIPE = {
    "post_style": {"length_words": [10, 20], "tone": "professional", "cta": "Click here!"}
}

# A sample recipe for a thread post
THREAD_RECIPE = {
    "post_style": {"length_words": [5, 10], "tone": "engaging", "cta": "Read more below!"},
    "comments_style": {"count": 2, "length_words": [5, 10], "stagger_seconds": [1, 2]},
}

@pytest.fixture
def mocker():
    """Provides access to unittest.mock for compatibility with pytest-mock usage."""
    return mock


@pytest.fixture
def mock_generator(mocker):
    """Mocks the ContentGenerator."""
    return mocker.Mock()

@pytest.fixture
def mock_fb_client(mocker):
    """Mocks the FacebookClient."""
    return mocker.Mock()

@pytest.fixture
def mock_protocol_enforcer(mocker):
    """Mocks the ProtocolEnforcer."""
    mock_enforcer = mocker.Mock()
    mock_enforcer.validate_content.return_value = True
    return mock_enforcer

def test_run_longform_cycle_success(mock_generator, mock_fb_client, mock_protocol_enforcer):
    """Tests the successful execution of a longform post cycle."""
    topic = "test topic"
    generated_content = "This is a generated post."
    post_id = "fb_post_123"

    mock_generator.generate_post.return_value = generated_content
    mock_fb_client.post_to_feed.return_value = post_id
    mock_protocol_enforcer.validate_content.return_value = True

    result = post_cycle.run_longform_cycle(
        topic, mock_generator, mock_fb_client, mock_protocol_enforcer, LONGFORM_RECIPE
    )

    mock_generator.generate_post.assert_called_once_with(topic, LONGFORM_RECIPE)
    mock_protocol_enforcer.validate_content.assert_called_once_with(generated_content)
    mock_fb_client.post_to_feed.assert_called_once_with(generated_content)
    assert result == post_id

def test_run_longform_cycle_generation_fails(mock_generator, mock_fb_client, mock_protocol_enforcer):
    """Tests that the cycle aborts if content generation fails."""
    mock_generator.generate_post.return_value = None

    result = post_cycle.run_longform_cycle(
        "topic", mock_generator, mock_fb_client, mock_protocol_enforcer, LONGFORM_RECIPE
    )

    assert result is None
    mock_fb_client.post_to_feed.assert_not_called()

def test_run_longform_cycle_validation_fails(mock_generator, mock_fb_client, mock_protocol_enforcer):
    """Tests that the cycle aborts if content validation fails."""
    mock_generator.generate_post.return_value = "Generated content."
    mock_protocol_enforcer.validate_content.return_value = False

    result = post_cycle.run_longform_cycle(
        "topic", mock_generator, mock_fb_client, mock_protocol_enforcer, LONGFORM_RECIPE
    )

    assert result is None
    mock_fb_client.post_to_feed.assert_not_called()

def test_run_thread_cycle_success(mocker, mock_generator, mock_fb_client, mock_protocol_enforcer):
    """Tests the successful execution of a thread post cycle."""
    mocker.patch("time.sleep") # Mock time.sleep to avoid delays
    topic = "thread topic"
    main_post_content = "Main post."
    comments = ["Comment 1.", "Comment 2."]
    post_id = "fb_post_456"
    comment_id_1 = "fb_comment_1"
    comment_id_2 = "fb_comment_2"

    mock_generator.generate_post.return_value = main_post_content
    mock_generator.generate_thread_comments.return_value = comments
    mock_fb_client.post_to_feed.return_value = post_id
    mock_fb_client.add_comment.side_effect = [comment_id_1, comment_id_2]
    mock_protocol_enforcer.validate_content.return_value = True

    result = post_cycle.run_thread_cycle(
        topic, mock_generator, mock_fb_client, mock_protocol_enforcer, THREAD_RECIPE
    )

    assert result == post_id
    mock_generator.generate_post.assert_called_once_with(topic, THREAD_RECIPE)
    mock_fb_client.post_to_feed.assert_called_once_with(main_post_content)
    mock_generator.generate_thread_comments.assert_called_once_with(topic, main_post_content, THREAD_RECIPE)

    # Check that add_comment was called for each comment
    assert mock_fb_client.add_comment.call_count == 2
    mock_fb_client.add_comment.assert_any_call(post_id, comments[0])
    mock_fb_client.add_comment.assert_any_call(post_id, comments[1])


def test_run_thread_cycle_returns_post_id_when_no_comments(
    mocker, mock_generator, mock_fb_client, mock_protocol_enforcer
):
    """Ensures cycles without generated comments still return the post ID."""
    mocker.patch("time.sleep")
    topic = "thread topic"
    main_post_content = "Main post."
    post_id = "fb_post_456"

    mock_generator.generate_post.return_value = main_post_content
    mock_generator.generate_thread_comments.return_value = []
    mock_fb_client.post_to_feed.return_value = post_id
    mock_protocol_enforcer.validate_content.return_value = True

    result = post_cycle.run_thread_cycle(
        topic, mock_generator, mock_fb_client, mock_protocol_enforcer, THREAD_RECIPE
    )

    assert result == post_id
    mock_fb_client.add_comment.assert_not_called()

def test_run_thread_cycle_post_fails(mock_generator, mock_fb_client, mock_protocol_enforcer):
    """Tests that the thread cycle aborts if the main post fails."""
    mock_generator.generate_post.return_value = "Main post."
    mock_fb_client.post_to_feed.return_value = None

    result = post_cycle.run_thread_cycle(
        "topic", mock_generator, mock_fb_client, mock_protocol_enforcer, THREAD_RECIPE
    )

    assert result is None
    mock_generator.generate_thread_comments.assert_not_called()
    mock_fb_client.add_comment.assert_not_called()