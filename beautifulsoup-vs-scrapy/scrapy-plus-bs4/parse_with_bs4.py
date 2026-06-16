"""
Scrapy + BeautifulSoup together.

A legitimate pattern, not a hack: let Scrapy do the crawling and concurrency,
then hand the raw HTML to BeautifulSoup inside the callback when a page has
messy or broken markup that BeautifulSoup tolerates better than strict parsers.

For clean pages like books.toscrape.com you don't need this — Scrapy's own
lxml-backed selectors are faster. It's here to show the integration point, which
is just `BeautifulSoup(response.text, ...)` inside parse().

Run:
    scrapy runspider parse_with_bs4.py -o books.csv
"""

import scrapy
from bs4 import BeautifulSoup


class BooksSpider(scrapy.Spider):
    name = "books_bs4"
    start_urls = ["https://books.toscrape.com/catalogue/page-1.html"]

    def parse(self, response):
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(href, self.parse_book)

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_book(self, response):
        # Scrapy fetched the page; BeautifulSoup parses it.
        soup = BeautifulSoup(response.text, "lxml")
        yield {
            "title": soup.select_one("div.product_main h1").get_text(strip=True),
            "price": soup.select_one("p.price_color").get_text(strip=True),
            "stock": soup.select_one("p.availability").get_text(strip=True),
        }
