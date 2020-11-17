#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/11/16 14:36
# @Author  : LiuJiang
# @File    : session.py
# @Software: PyCharm
import json

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util import Retry


class CrawlerSession:
    def __init__(self, server_domain, target_site_domain, protocol="http"):
        retry = Retry(total=5, method_whitelist=frozenset(["GET", "POST", "PATCH"]))
        adapter = HTTPAdapter(max_retries=retry)
        self.protocol = protocol
        self.session = requests.Session()
        self.session.auth = ("crawler", "@r8aK#75&pkEYQdf")
        self.session.mount(f"{self.protocol}://", adapter)

        self.server_domain = server_domain
        self.target_site_domain = target_site_domain

    def build_url(self, resource="houses", pk=None, action=None):
        if pk and isinstance(pk, int):
            return f"{self.protocol}://{self.server_domain}/v1/{resource}/{pk}/"
        elif action and isinstance(action, str):
            return f"{self.protocol}://{self.server_domain}/v1/{resource}/{action}/"
        return f"{self.protocol}://{self.server_domain}/v1/{resource}/"

    def get_out_of_date_list(self, hours=1, minutes=0, seconds=0):
        url = self.build_url()

        delta = f"{hours}H{minutes}M{seconds}S"
        status = "todo,doing"  # only update alive house
        page_size = 100

        params = {
            "out_of_date": delta,
            "status__in": status,
            "site_domain": self.target_site_domain,
            "page_size": page_size,
            "page": 1,
        }

        count = float("inf")
        results = []
        while len(results) < count:
            resp = self.list_item(url, params=params)
            if resp.status_code == 200:
                params["page"] += 1
                data = resp.json()
                count = data["count"]
                results.extend(
                    [
                        (item["id"], item["site_url"], item["site_id"], item["start"])
                        for item in data["results"]
                    ]
                )
            else:
                break

        return results

    def get_absent_list(self, data):
        site_id_set = [item["id"] for item in data]

        # url = "https://dev.gongxinzc.cn/v1/houses/absent/"
        url = self.build_url(action="absent")

        r = self.session.post(
            url,
            json={"site_id_set": site_id_set, "site_domain": self.target_site_domain},
        )
        result = json.loads(r.text)
        return result.get("absence", [])

    def get_ignore_list(self):
        try:
            return self._ignore
        except AttributeError:
            with open("/app/ignore/list.txt", "rt") as f:
                self._ignore = [int(line.split(",")[0]) for line in f.readlines()]
            return self._ignore


    def create_item(self, url, data, files=None):
        return self.session.post(url, json=data, files=files)

    def list_item(self, url, params=None):
        return self.session.get(url, params=params)



class RetrySession:
    def __init__(self):
        retry = Retry(total=5, method_whitelist=frozenset(["GET", "POST", "PATCH"]))
        adapter = HTTPAdapter(max_retries=retry)
        self.__session = requests.Session()
        self.__session.mount("http://", adapter)

    def get(self, url, **kwargs):
        return self.__session.get(url, **kwargs)
