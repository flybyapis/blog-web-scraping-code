"""
Your first Scrapy spider.

Scrapes quotes.toscrape.com (a sandbox the Scrapy team built for practice).
Grabs the quote text, author, and tags from every quote on the first page.
This is the "20 minutes to a working spider" payoff from the blog post.

Run it standalone (no scrapy project needed):
    scrapy runspider quotes_spider.py -o quotes.json

Explore selectors interactively first:
    scrapy shell "https://quotes.toscrape.com"

Blog post: https://flybyapis.com/blog/how-to-use-scrapy/
"""

import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com"]

    def parse(self, response):
        for quote in response.css("div.quote"):
            yield {
                "text": quote.css("span.text::text").get(),
                "author": quote.css("small.author::text").get(),
                "tags": quote.css("div.tags a.tag::text").getall(),
            }
