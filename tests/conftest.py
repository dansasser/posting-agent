import importlib
import os
from unittest import mock

import pytest

# Ensure required environment variables are available for modules that load
# configuration at import time.
os.environ.setdefault("FACEBOOK_PAGE_ID", "test_page")
os.environ.setdefault("FACEBOOK_USER_ACCESS_TOKEN", "test_token")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")

# Reload settings so that the defaults above are recognized during tests.
settings_module = importlib.import_module("app.configs.settings")
importlib.reload(settings_module)


class _SimpleMocker:
    """Lightweight substitute for pytest-mock's MockerFixture."""

    def __init__(self):
        self._patchers = []

    def Mock(self, *args, **kwargs):
        return mock.Mock(*args, **kwargs)

    def patch(self, target, *args, **kwargs):
        patcher = mock.patch(target, *args, **kwargs)
        mocked = patcher.start()
        self._patchers.append(patcher)
        return mocked

    def stopall(self):
        for patcher in reversed(self._patchers):
            patcher.stop()
        self._patchers.clear()


@pytest.fixture
def mocker():
    helper = _SimpleMocker()
    try:
        yield helper
    finally:
        helper.stopall()
