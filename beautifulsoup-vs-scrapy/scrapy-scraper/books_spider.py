"""
Scrapy spider (async, default settings).

Same job as the BeautifulSoup scrapers: crawl all 50 listing pages, follow each
book to its detail page, pull title/price/stock, write a CSV. The difference is
how little of this you have to write yourself — Scrapy handles concurrency,
scheduling, retries and export. This is the fast column in the benchmark.

Run it standalone (no scrapy project needed):
    scrapy runspider books_spider.py -o books.csv

Tune concurrency (default is 16 concurrent requests):
    scrapy runspider books_spider.py -o books.csv -s CONCURRENT_REQUESTS=32
"""

import scrapy


class BooksSpider(scrapy.Spider):
    name = "books"
    start_urls = ["https://books.toscrape.com/catalogue/page-1.html"]

    def parse(self, response):
        # follow each book on this listing page to its detail page
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(href, self.parse_book)

        # follow pagination to the next listing page
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_book(self, response):
        yield {
            "title": response.css("div.product_main h1::text").get(),
            "price": response.css("p.price_color::text").get(),
            "stock": response.css("p.availability::text").getall()[-1].strip(),
        }
