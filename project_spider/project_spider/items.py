# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class post(Item):
    """A container (dictionary-like object) for scraped data from CDI."""
    cdi = Field()
    title = Field()
    date = Field()
    source = Field()
    text = Field()
    url = Field()
    screenshot_url = Field()
    pass
