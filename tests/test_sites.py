
import pytest
import requests

from unittest.mock import Mock, patch
from fastapi import HTTPException

from app.news_parser.sites import (
    parse_news,
    parse_all_news,
    parse_article,
    fetch_page,
    fetch_and_parse_news,
    fetch_and_parse_all_news,
    fetch_and_save_news,
)


# -------------------------
# parse_news()
# -------------------------

def test_parse_news_returns_title_and_text():
    html = """
    <div class="lenta-item">
        <h2>Тестовий заголовок</h2>
        <p>Текст новини</p>
    </div>
    """

    result = parse_news(html)

    assert result["title"] == "Тестовий заголовок"
    assert result["text"] == "Текст новини"


def test_parse_news_returns_empty_values_without_card():
    result = parse_news("<html><body>Немає новин</body></html>")

    assert result == {"title": "", "text": ""}


# -------------------------
# parse_all_news()
# -------------------------

def test_parse_all_news_returns_news_list():
    html = """
    <div class="lenta-item">
        <a href="/news/1">
            <h2>Перша новина</h2>
        </a>
        <p>Опис першої новини</p>
        <span class="meta-datetime">11.11.2026</span>
    </div>

    <div class="lenta-item">
        <a href="/news/2">
            <h2>Друга новина</h2>
        </a>
        <p>Опис другої новини</p>
    </div>
    """

    result = parse_all_news(
        html,
        source="Highload",
        base_url="https://highload.tech/"
    )

    assert len(result) == 2
    assert result[0]["title"] == "Перша новина"
    assert result[0]["summary"] == "Опис першої новини"
    assert result[0]["url"] == "https://highload.tech/news/1"
    assert result[0]["source"] == "Highload"
    assert result[0]["published_at"] == "11.11.2026"


def test_parse_all_news_skips_cards_without_title_or_text():
    html = """
    <div class="lenta-item">
        <h2>Є заголовок</h2>
    </div>

    <div class="lenta-item">
        <p>Є текст</p>
    </div>
    """

    result = parse_all_news(
        html,
        source="Highload",
        base_url="https://highload.tech/"
    )

    assert result == []


def test_parse_all_news_returns_empty_list_without_cards():
    result = parse_all_news(
        "<html></html>",
        source="Highload",
        base_url="https://highload.tech/"
    )

    assert result == []


# -------------------------
# parse_article()
# -------------------------

def test_parse_article_returns_full_text():
    html = """
    <h1>Заголовок статті</h1>
    <div class="content-inner">
        <p>Перший абзац.</p>
        <p>Другий абзац.</p>
        <p>Підписуйтесь на нас у соцмережах.</p>
    </div>
    """

    result = parse_article(html)

    assert result["title"] == "Заголовок статті"
    assert "Перший абзац." in result["text"]
    assert "Другий абзац." in result["text"]
    assert "Підписуйтесь на нас" not in result["text"]


def test_parse_article_returns_empty_values_without_content():
    result = parse_article("<html><body>Немає статті</body></html>")

    assert result == {"title": "", "text": ""}


# -------------------------
# fetch_page()
# -------------------------

@patch("app.news_parser.sites.requests.get")
def test_fetch_page_returns_html(mock_get):
    mock_response = Mock()
    mock_response.text = "<html>Тест</html>"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_page("https://example.com")

    assert result == "<html>Тест</html>"
    mock_get.assert_called_once_with(
        "https://example.com",
        timeout=10
    )


@patch("app.news_parser.sites.requests.get")
def test_fetch_page_handles_http_error(mock_get):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = (
        requests.exceptions.HTTPError("404 Not Found")
    )
    mock_get.return_value = mock_response

    with pytest.raises(HTTPException) as error:
        fetch_page("https://example.com")

    assert error.value.status_code == 502


@patch("app.news_parser.sites.requests.get")
def test_fetch_page_handles_connection_error(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError(
        "Помилка з'єднання"
    )

    with pytest.raises(HTTPException) as error:
        fetch_page("https://example.com")

    assert error.value.status_code == 502


# -------------------------
# fetch_and_parse_news()
# -------------------------

@patch("app.news_parser.sites.fetch_page")
def test_fetch_and_parse_news(mock_fetch):
    mock_fetch.return_value = """
    <div class="lenta-item">
        <h2>Тестова новина</h2>
        <p>Текст новини</p>
    </div>
    """

    result = fetch_and_parse_news("https://example.com")

    assert result["title"] == "Тестова новина"
    assert result["text"] == "Текст новини"


# -------------------------
# fetch_and_parse_all_news()
# -------------------------

@patch("app.news_parser.sites.fetch_page")
def test_fetch_and_parse_all_news(mock_fetch):
    listing_html = """
    <div class="lenta-item">
        <a href="/news/1">
            <h2>Тестова новина</h2>
        </a>
        <p>Короткий опис</p>
    </div>
    """

    article_html = """
    <h1>Тестова новина</h1>
    <div class="content-inner">
        <p>Повний текст статті.</p>
    </div>
    """

    mock_fetch.side_effect = [listing_html, article_html]

    result = fetch_and_parse_all_news(
        source="Highload",
        base_url="https://highload.tech/"
    )

    assert len(result) == 1
    assert result[0]["title"] == "Тестова новина"
    assert result[0]["raw_text"] == "Повний текст статті."
    assert mock_fetch.call_count == 2


@patch("app.news_parser.sites.fetch_page")
def test_fetch_and_parse_all_news_skips_news_without_url(mock_fetch):
    listing_html = """
    <div class="lenta-item">
        <h2>Новина без посилання</h2>
        <p>Опис новини</p>
    </div>
    """

    mock_fetch.return_value = listing_html

    result = fetch_and_parse_all_news(
        source="Highload",
        base_url="https://highload.tech/"
    )

    assert result == []
    mock_fetch.assert_called_once()


# -------------------------
# fetch_and_save_news()
# -------------------------

@patch("app.news_parser.sites.create_many_news")
@patch("app.news_parser.sites.fetch_and_parse_all_news")
def test_fetch_and_save_news(mock_parse, mock_save):
    parsed_news = [
        {
            "title": "Тестова новина",
            "url": "https://example.com/news",
            "summary": "Опис",
            "source": "Highload",
            "published_at": "11.11.2026",
            "raw_text": "Повний текст",
        }
    ]

    mock_parse.return_value = parsed_news
    mock_save.return_value = {"saved": 1, "skipped": 0}

    db = Mock()

    result = fetch_and_save_news(
        db=db,
        source="Highload",
        base_url="https://highload.tech/"
    )

    assert result == {"saved": 1, "skipped": 0}
    mock_parse.assert_called_once_with(
        "Highload",
        "https://highload.tech/"
    )
    mock_save.assert_called_once_with(db, parsed_news)
