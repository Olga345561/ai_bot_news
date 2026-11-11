
from unittest.mock import patch, MagicMock

from app.ai.translator import translate_news


def test_translate_news():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        '{"title": "Новий заголовок", '
        '"summary": "Короткий опис українською", '
        '"raw_text": "Повний текст українською"}'
    )

    with patch(
        "app.ai.translator.client.chat.completions.create",
        return_value=mock_response
    ):
        result = translate_news(
            title="New technology",
            summary="A new technology was introduced",
            raw_text="The company introduced a new technology."
        )

    assert result["title"] == "Новий заголовок"
    assert result["summary"] == "Короткий опис українською"
    assert result["raw_text"] == "Повний текст українською"
