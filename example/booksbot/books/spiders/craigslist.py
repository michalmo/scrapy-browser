import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Compose, Join
from scrapy_browser.request import BrowserRequest


def strip(s):
    return s.strip()


class ProductItem(scrapy.Item):
    title = scrapy.Field(output_processor=Compose(TakeFirst(), strip))
    price = scrapy.Field(output_processor=Compose(TakeFirst(), strip))
    email = scrapy.Field(output_processor=Compose(TakeFirst(), strip))
    phone = scrapy.Field(output_processor=Compose(TakeFirst(), strip))
    description = scrapy.Field(output_processor=Compose(Join(), strip))
    lat = scrapy.Field(output_processor=Compose(TakeFirst(), strip))
    lng = scrapy.Field(output_processor=Compose(TakeFirst(), strip))
    posted = scrapy.Field(output_processor=Compose(TakeFirst(), strip))
    images = scrapy.Field()
    id = scrapy.Field(
        output_processor=Compose(Join(), strip, lambda p: p.split()[-1])
    )
    location = scrapy.Field(
        output_processor=Compose(Join(), lambda p: p.strip('()'))
    )


class CraigslistSpider(scrapy.Spider):
    name = 'craigslist'
    allowed_domains = ['craigslist.org']

    def start_requests(self):
        yield BrowserRequest(
            'https://washingtondc.craigslist.org/nva/cto/d/solid-car-for-good-price/6687882619.html',
            script=[
                {'action': 'wait', 'args': {'seconds': 0.5}},
                {'action': 'click', 'args': {'css_selector': '.reply_button'}},
                {'action': 'wait', 'args': {'seconds': 3}},
                {'action': 'extract'},
            ],
        )

    def parse(self, response):
        il = ItemLoader(selector=response, item=ProductItem())
        il.add_css('title', '#titletextonly::text')
        il.add_css('location', '.postingtitletext > small::text')
        il.add_css('price', '.price::text')
        il.add_css('phone', '.reply-tel-number::text')
        il.add_css('email', '.reply-email-address > a::text')
        il.add_css('description', '#postingbody::text')
        il.add_css('lat', '#map::attr(data-latitude)')
        il.add_css('lng', '#map::attr(data-longitude)')
        il.add_css('images', '.thumb::attr(href)')
        il.add_css('posted', '.timeago::attr(datetime)')
        return il.load_item()
