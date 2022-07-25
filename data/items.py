# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DataItem(scrapy.Item):
    # define the fields for your item here like:
    game_name = scrapy.Field()  # 游戏名称
    title = scrapy.Field()  # 商品标题
    type_merchandize = scrapy.Field()  # 商品种类
    price = scrapy.Field()  # 价格
    num_data = scrapy.Field()  # 商品库存
    game_area = scrapy.Field()  # 游戏/区/服
    date_time = scrapy.Field()  # 抓取时间
    unit_price = scrapy.Field()  # 单价
    gather_time = scrapy.Field()  # 交易时间
    data_type = scrapy.Field()  # 数据分类
    prop_name = scrapy.Field()  # 不同游戏的不同商品种类
    derivation = scrapy.Field()  # 数据来源
