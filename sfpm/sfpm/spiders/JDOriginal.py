# -*- coding: utf-8 -*-
import json
import random
import urllib
import faker
import pytz
import requests
import scrapy
from copy import deepcopy
from datetime import datetime
from ..items import SfpmItem
from ..session import CrawlerSession
from ..policy import CrawlerPolicy

cntz = pytz.timezone("Asia/Shanghai")


class JdoriginalSpider(scrapy.Spider):
    name = 'JDOriginal'
    # jd_mapping
    status_mapping = {0: "todo", 1: "doing", 2: "done"}
    status_detail_mapping = {
        # (auctionStatus, displayStatus,)
        (0, 1): lambda x: "todo",
        (1, 1): lambda x: "doing",
        (2, 1): lambda x: "deal" if x else "fail",
        (2, 5): lambda x: "other",
        (2, 6): lambda x: "other",
        (2, 7): lambda x: "other",
    }
    stage_mapping = {1: "HSG1", 2: "HSG2", 4: "HSG4"}

    # other
    base = "https://api.m.jd.com/api"
    img_hosts = [
        "img10.360buyimg.com",
        "img11.360buyimg.com",
        "img12.360buyimg.com",
        "img13.360buyimg.com",
        "img14.360buyimg.com",
    ]
    fake = faker.Faker()
    crawler_session = CrawlerSession(
        server_domain="api.cxiaoying.cn", target_site_domain="jd", protocol="https"
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
            # print('user_agent', user_agent)
            if "Android" in user_agent or "CriOS" in user_agent:
                continue
            else:
                break

        return {"user-agent": user_agent, "referer": referer}

    def start_requests(self):
        """
        开始请求调用build_list_urls请求
        :return:
        """
        self.urls = self.build_list_urls()
        url = next(self.urls)
        headers = self.headers(url)
        yield scrapy.Request(url, callback=self.parse, headers=headers)

    def build_list_urls(self):
        """
        创建广东省2018-01-01--2020-02-10时间断的url
        :return:
        """
        appid = "paimai-search-soa"
        functionId = "paimai_unifiedSearch"
        body = {
            "apiType": 2,
            "page": "1",
            "pageSize": 40,
            "reqSource": 0,
            "childrenCateId": "12728",  # 住宅用房
            "provinceId": 19,  # 广东
            # "cityId": 1601,  # 广州
            # "provinceId": 1,
            "timeRangeTime": "auditTime",
            "timeRangeStart": '2018-01-01',
            "timeRangeEnd": '2020-02-10'
        }
        loginType = 3

        # 下一页
        page = 1
        while True:
            body["page"] = str(page)
            yield self.__build_url(appid, functionId, body, loginType)
            page += 1

    def build_detail_url(self, site_id):
        """
        创建商品细节url
        :param site_id:
        :return:
        """
        appid = "paimai"
        functionId = "getProductBasicInfo"
        body = {"paimaiId": site_id}
        loginType = 3
        return self.__build_url(appid, functionId, body, loginType)

    def build_realtime_url(self, site_id):
        """
        创建实时url
        :param site_id:
        :return:
        """
        # realtime data
        # price_current, count_view, count_apply, status...
        appid = "paimai"
        functionId = "getPaimaiRealTimeData"
        body = {"end": 9, "paimaiId": site_id, "source": 0, "start": 0}
        loginType = 3
        return self.__build_url(appid, functionId, body, loginType)

    def build_announcement_url(self, album_id):
        """
        创建公告url
        :param album_id:
        :return:
        """
        appid = "paimai"
        functionId = "queryAnnouncement"
        body = {"albumId": album_id}
        loginType = 3
        return self.__build_url(appid, functionId, body, loginType)

    def build_notice_url(self, site_id):
        """
        创建商品描述url
        :param site_id:
        :return:
        """
        appid = "paimai"
        functionId = "queryNotice"
        body = {"paimaiId": site_id}
        loginType = 3
        notice_url = self.__build_url(appid, functionId, body, loginType)
        return notice_url

    def build_description_url(self, site_id):
        """
        chuangjianurl
        :param site_id:
        :return:
        """
        appid = "paimai"
        functionId = "queryProductDescription"
        body = {"paimaiId": site_id, "source": 0}
        loginType = 3
        return self.__build_url(appid, functionId, body, loginType)

    def __build_url(self, appid, functionId, body, loginType):
        """
        对url进行encoded
        :param appid:
        :param functionId:
        :param body:
        :param loginType:
        :return:
        """
        bodystr = "".join(json.dumps(body).split())
        bodystr = f"{{{urllib.parse.quote(bodystr[1:-1])}}}"
        qq = f"{self.base}?appid={appid}&functionId={functionId}&body={bodystr}&loginType={loginType}"
        # print(qq)
        return qq

    def build_image_url(self, path):
        """
        创建图片url
        :param path:
        :return:
        """
        if path is not None:
            return f"https://{random.choice(self.img_hosts)}/img/s350x350_{path}"

    def parse(self, response):
        json_data = json.loads(response.text)

        # absence = self.crawler_session.get_absent_list(json_data["datas"])
        # ignore = self.crawler_session.get_ignore_list()

        for item in self.crawler_policy.create_generator(
                self.crawler_session, data=json_data["datas"], get_site_id=lambda x: x["id"]
        ):
            # if item["id"] not in absence:
            #     self.logger.debug(f"Item {item['id']} already crawled, skip.")
            #             #     continue
            # if item["id"] in ignore:
            #     self.logger.info(f"Item {item['id']} is ignored. skip.")
            #     continue

            link = self.build_detail_url(item["id"])
            headers = self.headers(link)
            yield scrapy.Request(
                link,
                callback=self.parse_detail,
                headers=headers,
                meta={"item": item, "link": link},
            )

        # 请求下一页
        if json_data["statusCode"] == 200:
            if json_data["totalItem"] > json_data["page"] * json_data["pageSize"]:
                url = next(self.urls)
                headers = self.headers(url)
                yield scrapy.Request(url, callback=self.parse, headers=headers)

    def parse_detail(self, response):
        """
        解析商品详情页,构建
        :param response:
        :return:
        """
        link = response.meta["link"]
        item = response.meta["item"]
        item = deepcopy(item)
        item.update(json.loads(response.text)["data"])
        site_id = item["id"]
        album_id = item["albumId"]  # 公告id

        urls = {
            "realtime": self.build_realtime_url(site_id),
            "announcement": self.build_announcement_url(album_id),
            "notice": self.build_notice_url(site_id),
            "description": self.build_description_url(site_id),
        }

        headers = self.headers(link)
        yield scrapy.Request(
            urls["realtime"],
            callback=self.parse_realtime,
            meta={"item": item, "urls": urls, "headers": headers},
            headers=headers,
        )

    def parse_realtime(self, response):
        item = response.meta["item"]
        # print('response', item)
        urls = response.meta["urls"]

        obj = json.loads(response.text)["data"]
        item.update(obj)

        yield scrapy.Request(
            urls["announcement"],
            callback=self.parse_announcement,
            meta=response.meta,
            headers=response.meta["headers"],
        )

    def parse_announcement(self, response):
        item = response.meta["item"]
        urls = response.meta["urls"]

        obj = json.loads(response.text)["data"]
        item["announcement"] = obj["content"]

        yield scrapy.Request(
            urls["notice"],
            callback=self.parse_notice,
            meta=response.meta,
            headers=response.meta["headers"],
        )

    def parse_notice(self, response):
        item = response.meta["item"]
        urls = response.meta["urls"]

        obj = json.loads(response.text)["data"]
        item["notice"] = obj

        yield scrapy.Request(
            urls["description"],
            callback=self.parse_description,
            meta=response.meta,
            headers=response.meta["headers"],
        )

    def parse_description(self, response):
        item = response.meta["item"]

        obj = json.loads(response.text)["data"]
        item["description"] = obj

        yield self.jd_mapping(item)

    def jd_mapping(self, obj):
        price_marketing = obj["judicatureBasicInfoResult"].get("marketPrice", 0)
        price_consult = max(obj.get("assessmentPrice", 0), price_marketing)

        court_phone_list = obj["judicatureBasicInfoResult"]["consultTel"].split("/")
        court_phone = "/".join(court_phone_list[:2])
        item = SfpmItem(
            site_id=obj["id"],
            site_url=f"https://paimai.jd.com/{obj['id']}",
            site_domain="jd",
            court_name=obj["shopName"],
            court_phone=court_phone,
            title=obj["title"],
            province=obj["productAddressResult"].get("province"),
            city=obj["productAddressResult"].get("city"),
            district=obj["productAddressResult"].get("county"),
            address=obj["productAddressResult"].get("address"),
            status=self.status_mapping.get(obj["auctionStatus"]),
            status_detail=self.status_detail_mapping[
                obj["auctionStatus"], obj["displayStatus"]
            ](obj["bidCount"] > 0),
            stage=self.stage_mapping.get(obj["paimaiTimes"]),
            sell_off=obj["paimaiTimes"] == 4,
            start=datetime.fromtimestamp(obj["startTime"] / 1000, tz=cntz),
            end=datetime.fromtimestamp(obj["endTime"] / 1000, tz=cntz),
            cover=self.build_image_url(obj.get("productImage")),
            images=[
                self.build_image_url(item.get("imagePath"))
                for item in obj.get("paimaiImageResultList", [])
            ],
            price_initial=int(obj.get("startPrice", 0) * 100),
            price_current=int(obj.get("currentPrice", 0) * 100),
            price_consult=int(price_consult * 100),
            price_marketing=int(price_consult * 1.1),
            price_margin=int(obj.get("ensurePrice", 0) * 100),
            price_step=int(obj.get("priceLowerOffset", 0) * 100),
            count_view=obj.get("accessNum"),
            count_apply=obj.get("accessEnsureNum"),
            announcement=obj.get("announcement"),
            notice=obj.get("notice"),
            description=obj.get("description"),
        )
        # print(item)

        return item
