import requests
from fastapi import HTTPException
from bs4 import BeautifulSoup

def parse_news(html:str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # Знаходимо текст новини, за яким визначаємо картку
    news_text= soup.find(
        string=lambda text: text and "Розробники Python випустили версію 3.15" in text
    )

    if not news_text:
        return {"title":"",
                "text":"",}

    # Знаходимо картку конкретної новини
    news_card = news_text.find_parent(
        "div",
        class_="lenta-item")

    if not news_card:
        return {"title":"",
                "text":"",}

    # Витягуємо заголовок і текст
    title_tag = news_card.find("h2")
    text_tag = news_card.find("p", class_=None)
    title = title_tag.get_text(strip=True)if title_tag else ""
    text = text_tag.get_text(strip=True) if text_tag else ""
    return {"title":title,
            "text":text,}

    # article = soup.find(
    #     string=lambda text: text and "Розробники Python випустили версію 3.15" in text
    # )
    # print(article)
    #
    # title = soup.find("h1") or soup.find("h2") or soup.find("h3") or soup.find("h4")
    # paragraphs =soup.find_all("p")
    # text = "\n".join(
    #     paragraph.get_text(strip=True)
    #     for paragraph in paragraphs)
    #
    # return {"title":title.get_text(strip=True) if title else "",
    #         "text":text}

def parse_all_news(html:str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    news_card = soup.find_all("div", class_="lenta-item")

    news_list = []

    for news in news_card:
        title_tag = news.find("h2")
        text_tag = news.find("p", class_=None)

        title = title_tag.get_text(strip=True)if title_tag else ""
        text = text_tag.get_text(strip=True) if text_tag else ""
        if title and text:
            news_list.append({"title":title,
                              "text":text})
    return news_list




def fetch_page(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Не вдалося отримати сторінку: {e}")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Помилка під час запиту до сайту")

def fetch_and_parse_news(url:str) -> dict:
    html = fetch_page(url)
    news = parse_news(html)
    return news
