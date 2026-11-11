
from unittest.mock import patch, MagicMock

import pytest

from app.ai.generator import generate_post


@patch("app.ai.generator.client.chat.completions.create")
def test_generate_post_success(mock_create):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "  Тестовий допис про AI 🤖  "

    mock_create.return_value = mock_response

    result = generate_post(
        title="Новина про AI",
        text="Компанія представила нову модель штучного інтелекту."
    )

    assert result == "Тестовий допис про AI 🤖"

    mock_create.assert_called_once()

    call_kwargs = mock_create.call_args.kwargs

    assert call_kwargs["model"] == "gpt-5-nano"
    assert call_kwargs["messages"][0]["role"] == "system"
    assert call_kwargs["messages"][1]["role"] == "user"


@patch("app.ai.generator.client.chat.completions.create")
def test_generate_post_empty_response(mock_create):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = ""

    mock_create.return_value = mock_response

    with pytest.raises(ValueError, match="ШІ не повернув текст допису"):
        generate_post("Тестова новина", "Текст новини")


@patch("app.ai.generator.client.chat.completions.create")
def test_generate_post_none_response(mock_create):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = None

    mock_create.return_value = mock_response

    with pytest.raises(ValueError, match="ШІ не повернув текст допису"):
        generate_post("Тестова новина", "Текст новини")


@patch("app.ai.generator.client.chat.completions.create")
def test_generate_post_api_error(mock_create):
    mock_create.side_effect = Exception("Помилка OpenAI API")

    with pytest.raises(Exception, match="Помилка OpenAI API"):
        generate_post("Тестова новина", "Текст новини")
