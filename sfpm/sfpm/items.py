# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SfpmItem(scrapy.Item):
    site_id = scrapy.Field()
    site_url = scrapy.Field()
    site_domain = scrapy.Field()
    court_name = scrapy.Field()  # 法院名称
    court_phone = scrapy.Field()  # 法院电话
    title = scrapy.Field()  # 标题
    province = scrapy.Field()  # 省份
    city = scrapy.Field()  # 城市
    district = scrapy.Field()  # 联系地址
    address = scrapy.Field()  # 地址
    location_geo = scrapy.Field()  # 地理坐标，国标火星坐标系
    community = scrapy.Field()  # 小区名称
    area = scrapy.Field()  # a.k.a. 建筑面积
    area_building = scrapy.Field()  # 建筑面积
    area_saleable = scrapy.Field()  # 实用面积
    floor_current = scrapy.Field()  # 所在楼层
    floor_total = scrapy.Field()  # 建筑总楼层数
    facing = scrapy.Field()  # 朝向
    status = scrapy.Field()  # todo, doing, done 状态
    status_detail = scrapy.Field()  # todo, doing, deal, fail, other 状态细节
    stage = scrapy.Field()  # 一拍，二拍，变卖
    sell_off = scrapy.Field()  # 是否变卖
    start = scrapy.Field()  # 开始
    end = scrapy.Field()  # 结束
    cover = scrapy.Field()  # 覆盖
    images = scrapy.Field()  # 图片
    price_initial = scrapy.Field()  # 起拍价
    price_current = scrapy.Field()  # 当前价
    price_consult = scrapy.Field()  # 评估价
    price_marketing = scrapy.Field()  # 市场价
    price_margin = scrapy.Field()  # 保证金
    price_step = scrapy.Field()  # 加价幅度
    count_view = scrapy.Field()  # 围观人数
    count_apply = scrapy.Field()  # 报名人数
    announcement = scrapy.Field()  # 拍卖公告
    notice = scrapy.Field()  # 拍卖须知
    description = scrapy.Field()  # 标的物详情
    extra_params = scrapy.Field()  # 其他的必须参数
