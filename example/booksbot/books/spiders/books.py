import scrapy
from scrapy_browser.request import BrowserRequest


class BooksSpider(scrapy.Spider):
    name = 'books'
    allowed_domains = ['books.toscrape.com']

    def start_requests(self):
        yield BrowserRequest(
            'http://books.toscrape.com/',
            script=[
                {
                    'action': 'loop',
                    'args': {
                        'count': 50,
                        'script': [
                            {
                                'action': 'extract',
                            },
                            {
                                'action': 'click',
                                'args': {
                                    'css_selector': '.next a',
                                },
                            },
                            {
                                'action': 'wait',
                                'args': {
                                    'seconds': .1,
                                },
                            },
                        ],
                    },
                },
            ],
        )

    def parse(self, response):
        for book in response.css('article.product_pod'):
            yield {
                'title': book.css('h3 a::text').get(),
                'url': book.css('h3 a::attr(href)').get(),
            }
