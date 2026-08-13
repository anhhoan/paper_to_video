import requests
import re
from bs4 import BeautifulSoup
import trafilatura
from newspaper import Article
from core.models import ArticleSource

class ArticleScraper:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch(self, url: str) -> ArticleSource:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded, include_links=False, include_images=False, output_format='txt')
                if result and len(result.strip()) > 100:
                    return ArticleSource(text=result.strip(), url=url, origin="trafilatura")
        except Exception:
            pass

        try:
            article = Article(url)
            article.download()
            article.parse()
            if article.text and len(article.text.strip()) > 100:
                return ArticleSource(text=article.text.strip(), title=article.title, url=url, origin="newspaper3k")
        except Exception:
            pass

        try:
            resp = requests.get(url, timeout=self.timeout, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                container = soup.find('div', class_=re.compile(r'(fck_detail|detail-content|content_detail|post-content)')) or soup.find('body')
                paragraphs = [p.get_text().strip() for p in container.find_all('p') if len(p.get_text().strip()) > 20]
                full_text = "\n".join(paragraphs)
                if len(full_text) > 100:
                    return ArticleSource(text=full_text, url=url, origin="beautifulsoup")
        except Exception as e:
            raise RuntimeError(f"All scraper layers failed for URL {url}: {e}")

        raise ValueError(f"Could not extract content from {url}")