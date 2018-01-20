"""This module contains the items for the ``pybook`` package"""

import scrapy


class BookPageItem(scrapy.Item):
    page_index = scrapy.Field()
    volume_index = scrapy.Field()

    image_urls = scrapy.Field()
    images = scrapy.Field()
