# -*- coding: utf-8 -*-
import json
import re
import time
from datetime import datetime

import faker
import pytz
import scrapy

from ..items import SfpmItem
from ..session import CrawlerSession
from ..policy import CrawlerPolicy
from ..utils import ParseHelper

cntz = pytz.timezone("Asia/Shanghai")


class TaobaooriginalSpider(scrapy.Spider):
    name = 'taobaoOriginal'
    # taobao_mapping
    status_mapping = {
        "todo": "todo",
        "doing": "doing",
        "done": "done",
        "failure": "done",
        "break": "done",
        "revocation": "done",
    }
    status_detail_mapping = {
        "todo": "todo",
        "doing": "doing",
        "done": "deal",
        "failure": "fail",
        "break": "other",
        "revocation": "other",
    }
    stage_mapping = {
        "第一次拍卖": "HSG1",
        "第二次拍卖": "HSG2",
        "第一次": "HSG1",
        "第二次": "HSG2",
        "变卖": "HSG4",
    }
    texts_mapping = {
        "起拍价": "price_initial",
        "变卖价": "price_initial",
        "保证金": "price_margin",
        "评估价": "price_consult",
        "市场价": "price_consult",
        "加价幅度": "price_step",
    }

    # other
    fake = faker.Faker()
    crawler_session = CrawlerSession(
        server_domain="api.cxiaoying.cn",
        target_site_domain="taobao",
        protocol="https",
    )
    crawler_policy = CrawlerPolicy()

    def headers(self, referer):
        """
        删除移动标头，防止重定向302和解析失败
        :param referer:
        :return:
        """
        while True:
            user_agent = self.fake.chrome(
                version_from=63, version_to=80, build_from=999, build_to=3500
            )
            if "Android" in user_agent or "CriOS" in user_agent:
                continue
            else:
                break

        return {"user-agent": user_agent, "referer": referer}

    def start_requests(self):
        """
        请求一拍二拍和流拍网址信息
        :return:
        """
        start_date = '2012-01-01'
        end_date = '2020-03-01'
        urls_with_stage_filter = {
            "HSG1": f'https://sf.taobao.com/item_list.htm?spm=a213w.7398504.filter.25.5b831b7156pXlF&circ=1&category=50025969&auction_source=0&city=&province=%B9%E3%B6%AB&st_param=-1&auction_start_seg=0&auction_start_from={start_date}&auction_start_to={end_date}',
            "HSG2": f'https://sf.taobao.com/item_list.htm?spm=a213w.7398504.miniNav.2.289744fdOPgqe1&circ=%2C2&category=50025969&auction_source=0&province=%B9%E3%B6%AB&st_param=-1&auction_start_seg=0&auction_start_from={start_date}&auction_start_to={end_date}',
            "HSG4": f'https://sf.taobao.com/item_list.htm?spm=a213w.7398504.miniNav.3.2fa044fd185aIQ&circ=%2C4&category=50025969&auction_source=0&province=%B9%E3%B6%AB&st_param=-1&auction_start_seg=0&auction_start_from={start_date}&auction_start_to={end_date}',
        }

        for stage, url in urls_with_stage_filter.items():
            headers = self.headers(url)
            time.sleep(3)
            yield scrapy.Request(
                url, callback=self.parse, headers=headers, meta={"stage": stage}
            )
            time.sleep(3)

    def parse(self, response):
        """
        获取市区城市列表，再请求列表
        :param response:
        :return:
        """
        city_url_list = response.xpath(f'/html/body/div[3]/div[2]/ul[2]/li/div[2]/ul/li[20]/div/ul/li/em/a/@href')
        if city_url_list == []:
            city_url_list = response.xpath(f'/html/body/div[3]/div[2]/ul[2]/li/div[2]/ul/li[19]/div/ul/li/em/a/@href')
        for urls in city_url_list:
            url = "https:" + urls.get().strip()
            headers = self.headers(url)
            yield scrapy.Request(
                url, callback=self.parse_district, headers=headers, meta=response.meta
            )
            time.sleep(3)

    def parse_district(self, response):
        """
        获取城区列表，判断城区url是否为空，如果为空直接获取当前市的商品json，
        如果不为空循环请求区url
        :param response:
        :return:
        """
        district_url_list = response.xpath(
            "//div[@class='sub-condition J_SubCondition  small-subcondion']/ul/li/em/a/@href")
        if district_url_list == []:
            raw_data = response.xpath("//script[@id='sf-item-list-data']/text()").get()
            try:
                if len(raw_data) > 20:
                    json_data = json.loads(raw_data)
                    url = response.body_as_unicode()
                    for obj in self.crawler_policy.create_generator(
                            self.crawler_session, data=json_data["data"], get_site_id=lambda x: x["id"]
                    ):
                        item = SfpmItem()
                        item["stage"] = response.meta["stage"]
                        item["sell_off"] = response.meta["stage"] == "HSG4"
                        item["site_id"] = obj["id"]
                        item["site_url"] = page_url = f"https:{obj['itemUrl']}"
                        item["site_domain"] = "taobao"
                        item["title"] = obj["title"]
                        item["cover"] = f"https:{obj['picUrl']}"
                        item["price_initial"] = int(obj.get("initialPrice", 0) * 100)
                        item["price_current"] = int(obj.get("currentPrice", 0) * 100)
                        item["start"] = datetime.fromtimestamp(obj["start"] / 1000, tz=cntz)
                        item["end"] = datetime.fromtimestamp(obj["end"] / 1000, tz=cntz)
                        item["status"] = self.status_mapping.get(obj["status"])
                        item["status_detail"] = self.status_detail_mapping.get(obj["status"])
                        item["count_view"] = obj["viewerCount"]
                        item["count_apply"] = obj["applyCount"]
                        print('item', item)

                        headers = self.headers(page_url)
                        time.sleep(3)
                        yield scrapy.Request(
                            page_url,
                            callback=self.parse_detail,
                            meta={"item": item, "headers": headers},
                            headers=headers,
                        )
                        time.sleep(3)
                # 继续执行下一页
                next_element = response.xpath("//a[contains(@class, 'next')]/@href")  # 下一页
                print('执行第一下一页')
                if next_element:
                    url = "https:" + next_element.get().strip()
                    headers = self.headers(url)
                    yield scrapy.Request(
                        url, callback=self.parse, headers=headers, meta=response.meta
                    )
                    time.sleep(3)
            except:
                pass
        else:
            for urls in district_url_list:
                url = "https:" + urls.get().strip()
                headers = self.headers(url)
                time.sleep(3)
                yield scrapy.Request(
                    url, callback=self.parse_ctiy, headers=headers, meta=response.meta
                )

    def parse_ctiy(self, response):
        """
        获取json字符串，提取内容，再请求下一页
        :param response:
        :return:
        """
        raw_data = response.xpath("//script[@id='sf-item-list-data']/text()").get()
        try:
            if len(raw_data) > 20:
                json_data = json.loads(raw_data)
                url = response.body_as_unicode()
                for obj in self.crawler_policy.create_generator(
                        self.crawler_session, data=json_data["data"], get_site_id=lambda x: x["id"]
                ):
                    item = SfpmItem()
                    item["stage"] = response.meta["stage"]
                    item["sell_off"] = response.meta["stage"] == "HSG4"
                    item["site_id"] = obj["id"]
                    item["site_url"] = page_url = f"https:{obj['itemUrl']}"
                    item["site_domain"] = "taobao"
                    item["title"] = obj["title"]
                    item["cover"] = f"https:{obj['picUrl']}"
                    item["price_initial"] = int(obj.get("initialPrice", 0) * 100)
                    item["price_current"] = int(obj.get("currentPrice", 0) * 100)
                    item["start"] = datetime.fromtimestamp(obj["start"] / 1000, tz=cntz)
                    item["end"] = datetime.fromtimestamp(obj["end"] / 1000, tz=cntz)
                    item["status"] = self.status_mapping.get(obj["status"])
                    item["status_detail"] = self.status_detail_mapping.get(obj["status"])
                    item["count_view"] = obj["viewerCount"]
                    item["count_apply"] = obj["applyCount"]
                    print('item', item)

                    headers = self.headers(page_url)
                    time.sleep(3)
                    yield scrapy.Request(
                        page_url,
                        callback=self.parse_detail,
                        meta={"item": item, "headers": headers},
                        headers=headers,
                    )
            # 继续执行下一页
            next_element = response.xpath("//a[contains(@class, 'next')]/@href")  # 下一页
            print('执行第二下一页')
            if next_element:
                url = "https:" + next_element.get().strip()
                headers = self.headers(url)
                yield scrapy.Request(
                    url, callback=self.parse, headers=headers, meta=response.meta
                )
        except:
            pass



    def parse_detail(self, response):
        """
        获取商品详情页信息
        :param response:
        :return:
        """
        item = response.meta.pop("item")

        item["count_view"] = int(
            response.xpath("//*[@id='J_Looker']/text()").get().strip()
        )

        item["count_apply"] = int(
            response.xpath("//*[@class='J_Applyer']/text()").get().strip()
        )

        bian = response.xpath('//*[@id="page"]/div[4]/div/div/div[2]/div[1]/div/h1/text()').extract()
        for i in bian:
            bian_str = re.sub('\s+', '', i).strip()
            if len(bian_str) > 1:
                item["extra_params"] = bian_str


        # images
        item["images"] = self.replace(
            [
                f"https:{img_url}"
                for img_url in response.xpath(
                "//div[contains(@class, 'pm-pic')]//@src"
            ).getall()
            ]
        )

        item["court_name"] = (
            response.xpath("//*[contains(@class,'unit-name')]/a/text()").get().strip()  # 处置单位
        )

        court_phone_list = response.xpath(
            "//*[@class='contact-card']//*[@class='c-text']/text()"
        ).getall()
        item["court_phone"] = "/".join(court_phone_list[:2])  # 联系方式
        top_level = response.xpath("//*[@id='itemAddress']/text()").get().split()  # 标志物位置
        try:
            item["province"], item["city"], item["district"] = top_level
        except:
            if len(top_level) == 2:
                item["province"], item["city"] = top_level
            else:
                pass
                print(top_level)
        finally:
            item["address"] = (
                response.xpath("//*[@id='itemAddressDetail']/text()").get().strip()
            )

        urls = {
            "announcement": self.get_attach_url(response, "J_NoticeDetail"),  # 公告
            "notice": self.get_attach_url(response, "J_ItemNotice"),  # 购买须知
            "description": self.get_attach_url(response, "J_desc"),  # 标志物介绍
        }

        main_ct = ParseHelper.get_cleaned_text(response.css(".pm-main"))
        yield scrapy.Request(
            urls["announcement"],
            callback=self.parse_announcement,
            meta={"item": item, "urls": urls, "main_ct": main_ct, **response.meta},
            headers=response.meta["headers"],
        )

    def get_attach_url(self, response, tag_id):
        return "https:" + response.xpath(f"//*[@id='{tag_id}']/@data-from").get()

    def parse_announcement(self, response):
        item = response.meta.pop("item")

        result = re.search(r"({.*})", response.text)
        item["announcement"] = anno = json.loads(result.group(1))["content"]
        anno_ct = ParseHelper.get_cleaned_text(anno)

        headers = response.meta["headers"]
        yield scrapy.Request(
            response.meta["urls"]["notice"],
            callback=self.parse_notice,
            meta={"item": item, "anno_ct": anno_ct, **response.meta},
            headers=headers,
        )

    def parse_notice(self, response):
        item = response.meta.pop("item")

        result = re.search(r"({.*})", response.text)
        item["notice"] = noti = json.loads(result.group(1))["content"]
        noti_ct = ParseHelper.get_cleaned_text(noti)

        headers = response.meta["headers"]
        yield scrapy.Request(
            response.meta["urls"]["description"],
            callback=self.parse_description,
            meta={"item": item, "noti_ct": noti_ct, **response.meta},
            headers=headers,
        )

    def parse_description(self, response):
        item = response.meta.pop("item")
        item["description"] = desc = response.text[10:-2]
        desc_ct = ParseHelper.get_cleaned_text(desc)
        yield self.taobao_mapping(
            item,
            main_ct=response.meta["main_ct"],
            anno_ct=response.meta["anno_ct"],
            noti_ct=response.meta["noti_ct"],
            desc_ct=desc_ct,
        )

    def taobao_mapping(self, item, main_ct, anno_ct, noti_ct, desc_ct):

        for key, val in ParseHelper.bulk_parse_price(
                [main_ct, anno_ct, noti_ct, desc_ct],
                key_mapping={
                    "price_initial": 100,
                    "price_current": 100,
                    "price_consult": 100,
                    "price_margin": 100,
                    "price_step": 100,
                },
        ).items():
            item[key] = val
        else:
            item["price_marketing"] = int(item["price_consult"] / 100 * 1.1)
        for key, val in ParseHelper.bulk_parse_area(
                [main_ct, anno_ct, noti_ct, desc_ct]
        ).items():
            item[key] = val
        else:
            item["area"] = item["area_building"]

        return item

    def remove_duplicate(self, seq):
        # also keep originial order
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    def __replace(self, url):
        # translate thumbnail to bigger one
        return re.sub(r"_80x80", r"_460x460", url)

    def replace(self, urls):
        return self.remove_duplicate(list(map(self.__replace, urls)))
