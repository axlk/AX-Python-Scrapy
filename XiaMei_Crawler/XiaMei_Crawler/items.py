# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class XiaMeiPhotoAlbum(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
	album_name = scrapy.Field()
	album_desc = scrapy.Field()
	album_desc_info = scrapy.Field()
	create_time = scrapy.Field()
	photos = scrapy.Field()
