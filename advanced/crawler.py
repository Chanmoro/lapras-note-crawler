import json
import time
import dataclasses
from typing import List, Optional

import requests
from bs4 import BeautifulSoup


@dataclasses.dataclass(frozen=True)
class ArticleListPageParser:
    @dataclasses.dataclass(frozen=True)
    class ArticleListData:
        """
        記事一覧ページから取得されるデータを表すクラス
        """
        article_url_list: List[str]
        next_page_link: Optional[str]

    @classmethod
    def parse(self, html: str) -> ArticleListData:
        soup = BeautifulSoup(html, 'html.parser')
        next_page_link = soup.select_one("nav.navigation.pagination a.next.page-numbers")

        return self.ArticleListData(
            article_url_list=[a["href"] for a in soup.select("#main div.post-item h2 > a")],
            next_page_link=next_page_link["href"] if next_page_link else None
        )


@dataclasses.dataclass(frozen=True)
class ArticleDetailPageParser:
    @dataclasses.dataclass(frozen=True)
    class ArticleDetailData:
        """
        記事詳細ページから取得されるデータを表すクラス
        """
        title: str
        publish_date: str
        category: str
        content: str

    def parse(self, html: str) -> ArticleDetailData:
        soup = BeautifulSoup(html, 'html.parser')
        return self.ArticleDetailData(
            title=soup.select_one("h1").get_text(),
            publish_date=soup.select_one("article header div.entry-meta").find(text=True, recursive=False).replace("｜", ""),
            category=soup.select_one("article header div.entry-meta a").get_text(),
            content=soup.select_one("article div.entry-content").get_text(strip=True)
        )


@dataclasses.dataclass(frozen=True)
class LaprasNoteCrawler:
    INDEX_PAGE_URL = "https://note.lapras.com/"
    article_list_page_parser: ArticleListPageParser
    article_detail_page_parser: ArticleDetailPageParser

    def crawl_lapras_note_articles(self) -> List[ArticleDetailPageParser.ArticleDetailData]:
        """
        LAPRAS NOTE をクロールして記事のデータを全て取得する
        """
        return [self.crawl_article_detail_page(u) for u in self.crawl_article_list_page(self.INDEX_PAGE_URL)]

    def crawl_article_list_page(self, start_url: str) -> List[str]:
        """
        記事一覧ページをクロールして記事詳細の URL を全て取得する
        """
        print(f"Accessing to {start_url}...")
        # https://note.lapras.com/ へアクセスする
        response = requests.get(start_url)
        response.raise_for_status()
        time.sleep(10)

        # レスポンス HTML から記事詳細の URL を取得する
        page_data = self.article_list_page_parser.parse(response.text)
        article_url_list = page_data.article_url_list

        # 次ページのリンクがあれば取得する
        while page_data.next_page_link:
            print(f'Accessing to {page_data.next_page_link}...')
            response = requests.get(page_data.next_page_link)
            time.sleep(10)
            page_data = self.article_list_page_parser.parse(response.text)
            article_url_list += page_data.article_url_list

        return article_url_list

    def crawl_article_detail_page(self, url: str) -> ArticleDetailPageParser.ArticleDetailData:
        """
        記事詳細ページをクロールして記事のデータを取得する
        """
        # 記事詳細へアクセスする
        print(f"Accessing to {url}...")
        response = requests.get(url)
        response.raise_for_status()

        time.sleep(10)
        # レスポンス HTML から記事の情報を取得する
        return self.article_detail_page_parser.parse(response.text)


def collect_lapras_note_articles_usecase(crawler: LaprasNoteCrawler):
    """
    LAPRAS NOTE の記事のデータを全て取得してファイルに保存する
    """
    print("Start crawl LAPRAS NOTE.")
    article_list = crawler.crawl_lapras_note_articles()

    output_json_path = "./articles.json"
    with open(output_json_path, mode="w") as f:
        print(f"Start output to file. path: {output_json_path}")
        article_data = [dataclasses.asdict(d) for d in article_list]
        json.dump(article_data, f)
        print("Done output.")

    print("Done crawl LAPRAS NOTE.")


if __name__ == '__main__':
    collect_lapras_note_articles_usecase(LaprasNoteCrawler(
        article_list_page_parser=ArticleListPageParser(),
        article_detail_page_parser=ArticleDetailPageParser(),
    ))
