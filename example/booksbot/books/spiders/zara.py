import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Compose
from scrapy_browser.request import BrowserRequest


class ProductItem(scrapy.Item):
    name = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(output_processor=TakeFirst())
    sale_price = scrapy.Field(output_processor=TakeFirst())
    color = scrapy.Field(output_processor=TakeFirst())
    reference = scrapy.Field(output_processor=TakeFirst())
    images = scrapy.Field()
    sizes = scrapy.Field()


class SizeItem(scrapy.Item):
    size = scrapy.Field(output_processor=TakeFirst())
    in_stock = scrapy.Field(
        output_processor=Compose(TakeFirst(), lambda c: 'disabled' not in c)
    )
    sku = scrapy.Field(output_processor=TakeFirst())


class ZaraSpider(scrapy.Spider):
    name = 'zara'
    allowed_domains = ['zara.com']

    def start_requests(self):
        yield BrowserRequest(
            'https://www.zara.com/ie/en/jogging-trousers-p05536111.html',
            script=[
                {'action': 'wait', 'args': {'seconds': 2}},
                {
                    'action': 'while',
                    'args': {
                        'selector': '._color:nth-child({index}) > .color-description',
                        'start': 2,
                        'script': [
                            {'action': 'extract'},
                            {'action': 'click', 'args': {}},
                            {'action': 'wait', 'args': {'seconds': 1}},
                        ],
                    },
                },
                {'action': 'extract'},
            ],
        )

    def parse(self, response):
        il = ItemLoader(selector=response, item=ProductItem())
        il.add_css('name', '.product-name::text')
        il.add_css(
            'price', '.product-info-section .price > span:nth-child(1)::text'
        )
        il.add_css('sale_price', '.price > .sale::text')
        il.add_css('color', '._colorName::text')
        il.add_css('reference', '.reference::text')
        il.add_css('images', '.media-wrap > a > img::attr(src)')
        for size in response.css('.product-info-section .product-size'):
            sl = ItemLoader(selector=size, item=SizeItem())
            sl.add_css('size', '.size-name::text')
            sl.add_xpath('in_stock', './@class')
            sl.add_xpath('sku', './@data-sku')
            il.add_value('sizes', sl.load_item())
        return il.load_item()
