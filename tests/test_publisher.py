
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.telegram.publisher import publish_post


@pytest.mark.asyncio
@patch("app.telegram.publisher.get_telegram_client")
async def test_publish_post_success(mock_get_client):
    mock_client = MagicMock()

    mock_client.connect = AsyncMock()
    mock_client.is_user_authorized = AsyncMock(return_value=True)
    mock_client.send_message = AsyncMock(
        return_value=MagicMock(id=123)
    )
    mock_client.is_connected.return_value = True
    mock_client.disconnect = AsyncMock()

    mock_get_client.return_value = mock_client

    result = await publish_post("Тестовий допис 🤖")

    assert result == {
        "ok": True,
        "message_id": 123
    }

    mock_client.connect.assert_awaited_once()
    mock_client.is_user_authorized.assert_awaited_once()
    mock_client.send_message.assert_awaited_once_with(
        "@ai_news_today_ua",
        "Тестовий допис 🤖"
    )
    mock_client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.telegram.publisher.get_telegram_client")
async def test_publish_post_unauthorized(mock_get_client):
    mock_client = MagicMock()

    mock_client.connect = AsyncMock()
    mock_client.is_user_authorized = AsyncMock(return_value=False)
    mock_client.is_connected.return_value = True
    mock_client.disconnect = AsyncMock()

    mock_get_client.return_value = mock_client

    with pytest.raises(RuntimeError, match="Потрібна авторизація Telegram!"):
        await publish_post("Тестовий допис")

    mock_client.send_message.assert_not_called()
    mock_client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.telegram.publisher.get_telegram_client")
async def test_publish_post_send_error(mock_get_client):
    mock_client = MagicMock()

    mock_client.connect = AsyncMock()
    mock_client.is_user_authorized = AsyncMock(return_value=True)
    mock_client.send_message = AsyncMock(
        side_effect=Exception("Помилка відправлення")
    )
    mock_client.is_connected.return_value = True
    mock_client.disconnect = AsyncMock()

    mock_get_client.return_value = mock_client

    with pytest.raises(Exception, match="Помилка відправлення"):
        await publish_post("Тестовий допис")

    mock_client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.telegram.publisher.get_telegram_client")
async def test_publish_post_disconnects_after_error(mock_get_client):
    mock_client = MagicMock()

    mock_client.connect = AsyncMock(
        side_effect=Exception("Помилка підключення")
    )
    mock_client.is_connected.return_value = False
    mock_client.disconnect = AsyncMock()

    mock_get_client.return_value = mock_client

    with pytest.raises(Exception, match="Помилка підключення"):
        await publish_post("Тестовий допис")

    mock_client.disconnect.assert_not_awaited()
