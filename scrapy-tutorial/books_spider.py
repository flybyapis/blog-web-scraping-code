"""
A real Scrapy spider: following links + pagination + export.

Scrapes books.toscrape.com (another practice sandbox, this one with a full
catalog). Crawls every listing page, follows each book to its detail page, and
pulls the full record. This is the pattern behind ~80% of real-world scraping.

Run it and export to CSV in one command:
    scrapy runspider books_spider.py -o books.csv

Other formats work the same way (Scrapy picks from the file extension):
    scrapy runspider books_spider.py -o books.json    # JSON array
    scrapy runspider books_spider.py -o books.jl       # JSON Lines (best for big crawls)

Be polite on real sites (this sandbox is fine to hit):
    scrapy runspider books_spider.py -o books.csv -s DOWNLOAD_DELAY=1 -s AUTOTHROTTLE_ENABLED=True

Blog post: https://flybyapis.com/blog/how-to-use-scrapy/
"""

import scrapy


class BooksSpider(scrapy.Spider):
    name = "books"
    start_urls = ["https://books.toscrape.com/catalogue/page-1.html"]

    # Optional: uncomment for a polite, production-friendly crawl.
    # custom_settings = {
    #     "USER_AGENT": "Mozilla/5.0 (compatible; scrapy-tutorial/1.0)",
    #     "DOWNLOAD_DELAY": 1.0,
    #     "AUTOTHROTTLE_ENABLED": True,
    #     "RETRY_TIMES": 3,
    #     "ROBOTSTXT_OBEY": True,
    #     "FEEDS": {"books.csv": {"format": "csv", "encoding": "utf8", "overwrite": True}},
    # }

    def parse(self, response):
        # follow each book on this listing page to its detail page
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(href, self.parse_book)

        # follow pagination to the next listing page
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_book(self, response):
        availability = response.css("p.availability::text").getall()
        yield {
            "title": response.css("div.product_main h1::text").get(),
            "price": response.css("p.price_color::text").get(),
            # the sandbox always has this element; guard it on real sites
            "stock": availability[-1].strip() if availability else None,
        }
