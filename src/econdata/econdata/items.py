# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EcondataItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

import scrapy

class ExchangeRateItem(scrapy.Item):
    base_currency = scrapy.Field()
    target_currency = scrapy.Field()
    exchange_rate = scrapy.Field()
    last_updated_unix = scrapy.Field()
    last_updated_utc = scrapy.Field()