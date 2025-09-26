import requests

from app.adapters.facebook_client import FacebookClient


def test_send_direct_message_success(mocker):
    client = FacebookClient(page_id="page123", access_token="token123")
    mock_session = mocker.Mock()
    client.session = mock_session

    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "recipient_id": "user456",
        "message_id": "mid.789",
    }
    mock_response.raise_for_status.return_value = None
    mock_session.request.return_value = mock_response

    message_id = client.send_direct_message("user123", "Hello there!")

    assert message_id == "mid.789"
    mock_session.request.assert_called_once()
    method, url = mock_session.request.call_args[0][:2]
    kwargs = mock_session.request.call_args[1]
    assert method == "POST"
    assert url == f"{client.BASE_URL}/{client.page_id}/messages"
    assert kwargs["json"] == {
        "recipient": {"id": "user123"},
        "message": {"text": "Hello there!"},
        "messaging_type": "RESPONSE",
    }
    assert kwargs["params"]["access_token"] == "token123"


def test_send_direct_message_failure_returns_none(mocker):
    client = FacebookClient(page_id="page123", access_token="token123")
    mock_session = mocker.Mock()
    client.session = mock_session
    mock_session.request.side_effect = requests.exceptions.RequestException("boom")

    message_id = client.send_direct_message("user123", "Hello there!")

    assert message_id is None
    mock_session.request.assert_called_once()
