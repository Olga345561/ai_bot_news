
from unittest.mock import patch

from app.telegram import bot


@patch("app.telegram.bot.TelegramClient")
def test_get_telegram_client_creates_client(mock_client):
    result = bot.get_telegram_client()

    mock_client.assert_called_once_with(
        bot.SESSION_PATH,
        bot.API_ID,
        bot.API_HASH,
    )

    assert result == mock_client.return_value