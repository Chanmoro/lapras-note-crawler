import json
import time

import requests
from bs4 import BeautifulSoup


def parse_article_list_page(html):
    """
    記事一覧ページをパースしてデータを抜き出す
    :param html:
    :return:
    """
    soup = BeautifulSoup(html, 'html.parser')
    next_page_link = soup.select_one("nav.navigation.pagination a.next.page-numbers")

    return {
        "article_url_list": [a["href"] for a in soup.select("#main div.post-item h2 > a")],
        "next_page_link": next_page_link["href"] if next_page_link else None
    }


def crawl_article_list_page(start_url):
    """
    記事一覧ページをクロールして記事詳細の URL を全て取得する
    :return:
    """
    print(f"Accessing to {start_url}...")
    # https://note.lapras.com/ へアクセスする
    response = requests.get(start_url)
    response.raise_for_status()
    time.sleep(10)

    # レスポンス HTML から記事詳細の URL を取得する
    page_data = parse_article_list_page(response.text)
    article_url_list = page_data["article_url_list"]

    # 次ページのリンクがあれば取得する
    while page_data["next_page_link"]:
        print(f'Accessing to {page_data["next_page_link"]}...')
        response = requests.get(page_data["next_page_link"])
        time.sleep(10)
        page_data = parse_article_list_page(response.text)
        article_url_list += page_data["article_url_list"]

    return article_url_list


def parse_article_detail(html):
    """
    記事詳細ページをパースしてデータを抜き出す
    :param html:
    :return:
    """
    soup = BeautifulSoup(html, 'html.parser')
    return {
        "title": soup.select_one("h1").get_text(),
        "publish_date": soup.select_one("article header div.entry-meta").find(text=True, recursive=False).replace("｜", ""),
        "category": soup.select_one("article header div.entry-meta a").get_text(),
        "content": soup.select_one("article div.entry-content").get_text(strip=True)
    }


def crawl_article_detail_page(url):
    """
    記事詳細ページをクロールして記事のデータを取得する
    :param url:
    :return:
    """
    # 記事詳細へアクセスする
    print(f"Accessing to {url}...")
    response = requests.get(url)
    response.raise_for_status()

    time.sleep(10)
    # レスポンス HTML から記事の情報を取得する
    return parse_article_detail(response.text)


def crawl_lapras_note_articles(start_url):
    """
    LAPRAS NOTE をクロールして記事のデータを全て取得する
    :return:
    """
    article_url_list = crawl_article_list_page(start_url)
    article_list = []
    for article_url in article_url_list:
        article_data = crawl_article_detail_page(article_url)
        article_list.append(article_data)
    return article_list


def collect_lapras_note_articles():
    """
    LAPRAS NOTE の記事のデータを全て取得してファイルに保存する
    :return:
    """
    print("Start crawl LAPRAS NOTE.")
    article_list = crawl_lapras_note_articles("https://note.lapras.com/")

    output_json_path = "./articles.json"
    with open(output_json_path, mode="w") as f:
        print(f"Start output to file. path: {output_json_path}")
        json.dump(article_list, f)
        print("Done output.")

    print("Done crawl LAPRAS NOTE.")


if __name__ == '__main__':
    collect_lapras_note_articles()
