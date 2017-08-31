# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item
from scrapy import Field


class CompanyDivItem(Item):
    company_detail_div = Field()
    details_div = Field()
    pass


class DoubanbookIndexItem(Item):
    tagTitle = Field()
    tagItem = Field()


class DoubanbookItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    bookTitle = Field()
    bookAuthor = Field()
    bookPress = Field()
    bookDate = Field()
    bookPrice = Field()
    bookRatingNums = Field()
    bookRatingPl = Field()
    bookIntroduction = Field()
    pass


class QHCompanyDivOneItem(Item):
    company_id = Field()
    basic_center_div = Field()


class QHCompanyDivTwoItem(Item):
    company_id = Field()
    baseinfo_div = Field()
