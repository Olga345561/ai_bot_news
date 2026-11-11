
import pytest

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from app.news_parser.telegram import parse_telegram_messages, main


@pytest.fixture
def anyio_backend():
    return "asyncio"


def make_message(message_id, text):
    message = Mock()
    message.id = message_id
    message.message = text
    message.date = datetime(2026, 11, 11, tzinfo=timezone.utc)
    return message


async def async_messages(messages):
    for message in messages:
        yield message


# -------------------------
# parse_telegram_messages()
# -------------------------

@pytest.mark.anyio
async def test_parse_telegram_messages_returns_news():
    client = Mock()

    messages = [
        make_message(
            101,
            "Новий реліз Python\nВийшло оновлення для розробників."
        )
    ]

    client.iter_messages.return_value = async_messages(messages)

    result = await parse_telegram_messages(
        client=client,
        channel="ua_1techno",
        source="Перший Технологічний",
        limit=30,
    )

    assert len(result) == 1
    assert result[0]["title"] == "Новий реліз Python"
    assert result[0]["summary"] == "Вийшло оновлення для розробників."
    assert result[0]["url"] == "https://t.me/ua_1techno/101"
    assert result[0]["source"] == "Перший Технологічний"
    assert result[0]["raw_text"] == (
        "Новий реліз Python\nВийшло оновлення для розробників."
    )


@pytest.mark.anyio
async def test_parse_telegram_messages_uses_title_as_summary():
    client = Mock()

    messages = [
        make_message(102, "Новина без додаткового опису")
    ]

    client.iter_messages.return_value = async_messages(messages)

    result = await parse_telegram_messages(
        client,
        "ua_1techno",
        "Test",
    )

    assert len(result) == 1
    assert result[0]["summary"] == result[0]["title"]


@pytest.mark.anyio
async def test_parse_telegram_messages_skips_empty_messages():
    client = Mock()

    messages = [
        make_message(103, ""),
        make_message(104, None),
        make_message(105, "Корисна новина\nТекст новини"),
    ]

    client.iter_messages.return_value = async_messages(messages)

    result = await parse_telegram_messages(
        client,
        "ua_1techno",
        "Test",
    )

    assert len(result) == 1
    assert result[0]["title"] == "Корисна новина"


@pytest.mark.anyio
async def test_parse_telegram_messages_returns_empty_list():
    client = Mock()
    client.iter_messages.return_value = async_messages([])

    result = await parse_telegram_messages(
        client,
        "ua_1techno",
        "Test",
    )

    assert result == []


@pytest.mark.anyio
async def test_parse_telegram_messages_raises_error():
    client = Mock()

    async def failed_messages():
        raise RuntimeError("Помилка отримання повідомлень")
        yield

    client.iter_messages.return_value = failed_messages()

    with pytest.raises(RuntimeError):
        await parse_telegram_messages(
            client,
            "ua_1techno",
            "Test",
        )


# -------------------------
# main()
# -------------------------

@pytest.mark.anyio
@patch("app.news_parser.telegram.create_many_news")
@patch("app.news_parser.telegram.SessionLocal")
@patch("app.news_parser.telegram.parse_telegram_messages")
@patch("app.news_parser.telegram.get_telegram_client")
async def test_main_parses_and_saves_news(
    mock_get_client,
    mock_parse,
    mock_session,
    mock_save,
):
    client = Mock()
    client.connect = AsyncMock()
    client.is_user_authorized = AsyncMock(return_value=True)
    client.disconnect = AsyncMock()
    client.is_connected.return_value = True

    mock_get_client.return_value = client

    news_list = [
        {
            "title": "Тестова новина",
            "url": "https://t.me/ua_1techno/101",
            "summary": "Опис новини",
            "source": "Test",
            "published_at": "2026-11-11T00:00:00+00:00",
            "raw_text": "Тестова новина\nОпис новини",
        }
    ]

    mock_parse.return_value = news_list
    mock_save.return_value = {"saved": 1, "skipped": 0}

    db = Mock()
    mock_session.return_value = db

    result = await main(
        channel="ua_1techno",
        source="Test",
        limit=30,
    )

    assert result == {"saved": 1, "skipped": 0}

    mock_get_client.assert_called_once()
    client.connect.assert_awaited_once()
    client.is_user_authorized.assert_awaited_once()

    mock_parse.assert_awaited_once_with(
        client,
        "ua_1techno",
        "Test",
        30,
    )

    mock_save.assert_called_once_with(db, news_list)
    db.close.assert_called_once()
    client.disconnect.assert_awaited_once()


@pytest.mark.anyio
@patch("app.news_parser.telegram.get_telegram_client")
async def test_main_raises_error_when_not_authorized(mock_get_client):
    client = Mock()
    client.connect = AsyncMock()
    client.is_user_authorized = AsyncMock(return_value=False)
    client.disconnect = AsyncMock()
    client.is_connected.return_value = True

    mock_get_client.return_value = client

    with pytest.raises(RuntimeError, match="Потрібна авторизація Telegram"):
        await main(
            channel="ua_1techno",
            source="Test",
        )

    client.disconnect.assert_awaited_once()
