# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import json
import re

from .console import console
from .session import RetrySession
from .utils import ParseHelper, RebuildTable


class SfpmPipeline(object):
    extra = ["announcement", "notice", "description"]

    def process_item(self, item, spider):
        if spider.name.endswith("Original"):

            data_basic = {k: v for k, v in item.items() if k not in self.extra}
            data_extra = {k: v for k, v in item.items() if k in self.extra}
            try:
                url = spider.crawler_session.build_url()
                r = spider.crawler_session.create_item(url, data_basic)
                result = json.loads(r.text)

                data_extra["house"] = result["id"]

                url = spider.crawler_session.build_url(resource="house-extras")
                r = spider.crawler_session.create_item(url, data_extra)

            except Exception as e:
                spider.logger.error(f"{result}\n{data_basic['site_url']}")
                with open("/ignore/list.txt", "at") as f:
                    print("*" * 1000)
                    print(
                        f"{data_basic['site_id']},{data_basic['title']},{result}",
                        file=f,
                    )

        if spider.name.endswith("Update"):

            url = spider.crawler_session.build_url(pk=item["id"])
            data = dict(item)

            try:
                spider.crawler_session.update_item(url, data)
            except Exception as e:
                spider.logger.error(e)

        return item


class DataExtractPipeline:
    building_area_re = re.compile(r"面积.*?([-+]?[0-9]*\.?[0-9]+)(平方米|㎡|m2)")
    province_list = [
        "北京", "上海", "天津", "重庆", "河北", "山西", "河南", "辽宁", "吉林", "黑龙江",
        "内蒙古", "江苏", "山东", "安徽", "浙江", "福建", "湖北", "湖南", "广东", "广西",
        "江西", "四川", "海南", "贵州", "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆",
    ]
    province_normalize_re = re.compile(f"({'|'.join(province_list)})")

    def process_item(self, item, spider):
        if spider.name.endswith("Original"):
            item["start"] = str(item["start"])
            item["end"] = str(item["end"])

            if item.get("area") != None:
                ParseHelper.get_cleaned_text(item["announcement"])

            item["province"] = self.top_level_address_normalize(item["province"])

            try:
                # Rebuild tables in description
                item["description"] = RebuildTable.build_inline(item["description"])
            except Exception as e:
                spider.logger.error(e)

            self.area_setdefault(item)
            self.price_current_setdefault(item)

        return item

    def top_level_address_normalize(self, province):
        return self.province_normalize_re.search(province).group(1)

    def area_setdefault(self, item):
        if item.get("area") != None:
            return

        anno_ct = ParseHelper.get_cleaned_text(item["announcement"])
        desc_ct = ParseHelper.get_cleaned_text(item["description"])
        for key, value in ParseHelper.bulk_parse_area(
                [anno_ct, desc_ct], default=None
        ).items():
            item[key] = value
        else:
            item["area"] = item["area_building"]

    def price_current_setdefault(self, item):
        if item.get("price_current", 0) < 10:
            item["price_current"] = item["price_initial"]


class AmapGeoPipeline:
    key = "26ac797f95b4b1b4790a0ad5fc30a0cc"
    url = {
        "keywords-search": "https://restapi.amap.com/v3/place/text",
        "around-search": "https://restapi.amap.com/v3/place/around",
        "geo-encode": "https://restapi.amap.com/v3/geocode/geo",
        "geo-decode": "https://restapi.amap.com/v3/geocode/regeo",
    }
    session = RetrySession()

    def get(self, service, **kwargs):
        payload = {"key": self.key, **kwargs}
        return self.session.get(self.url[service], params=payload).json()

    def process_item(self, item, spider):

        if spider.name.endswith("Original"):
            location = f"{item.get('province', '')}{item.get('city', '')}{item.get('district', '')}{item.get('address', '')}"
            if len(location) < 4:
                spider.logger.info(f"location={location} too short, use title instead.")
                location = item.get("title")

            try:
                data = self.get("geo-encode", address=location)["geocodes"][0]
                item["location_geo"] = location_geo = data["location"]
                # item["province"] = province = data["province"]
                # item["city"] = city = data["city"]
                # item["district"] = district = data["district"]
                # if not item.get("district", ""):
                #     raise DropItem

                # if not item.get("address", ""):
                #     pattern = (
                #         f"(?P<province>{province})?"
                #         f"(?P<city>{city})?"
                #         f"(?P<district>{district})?"
                #         f"(?P<address>.+)"
                #     )
                #     item["address"] = re.match(pattern, location).group("address")
            except:
                console.print_exception()
                spider.logger.error(data)

            try:
                data = self.get("around-search", location=location_geo, types="住宅区")
                item["community"] = data["pois"][0]["name"]
            except:
                console.print_exception()
                spider.logger.error(data)

        return item
