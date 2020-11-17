#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/11/16 14:36
# @Author  : LiuJiang
# @File    : policy.py
# @Software: PyCharm
import logging
from typing import Iterator

from .console import console
from .session import CrawlerSession
from datetime import datetime, timedelta

DEFAULT_POLICY_SETTINGS = {
    "NEW": {"ABSENT": True, "IGNORE": False},
    "UPDATE": {
        "OUT_OF_DATE": [
            {"FILTER": "Before", "DIFF": "32H", },
            {"FILTER": "During", "DIFF": "16M", },
        ]
    },
}


class CrawlerPolicy:
    def __init__(self) -> None:
        self.policy = DEFAULT_POLICY_SETTINGS

    def get_ignore_list(self):
        try:
            return self._ignore
        except AttributeError:
            try:
                with open("/history_crawler/ignore/list.txt", "rt") as f:
                    self._ignore = [int(line.split(",")[0]) for line in f.readlines()]
            except:
                console.print_exception()
                self._ignore = []
            return self._ignore

    def extract_fields(self, data, fields):
        for row in data["results"]:
            yield [row[f] for f in fields]

    def fetch_data(
            self, crawler_session: CrawlerSession, params: dict, fields: Iterator
    ):
        url = crawler_session.build_url()

        params.setdefault("page", 1)
        params.setdefault("page_size", 100)
        params.setdefault("site_domain", crawler_session.target_site_domain)

        while True:
            response = crawler_session.list_item(url, params=params)
            if response.status_code == 200:
                params["page"] += 1
                yield from self.extract_fields(response.json(), fields=fields)
            elif response.status_code == 404:
                break
            else:
                raise RuntimeError(f"status_code={response.status_code}")

    def create_generator(
            self, crawler_session: CrawlerSession, data: list, get_site_id: callable,
    ):

        ignore = set(self.get_ignore_list())
        pk_set = set(get_site_id(obj) for obj in data)

        url = crawler_session.build_url(action="absent")

        r = crawler_session.session.post(
            url,
            json={
                "site_id_set": list(pk_set - ignore),
                "site_domain": crawler_session.target_site_domain,
            },
        )
    # try:
        result = r.json()
        logging.debug(result)
        absence = [str(a) for a in result.get("absence", [])]
        for obj in data:
            if (site_id := str(get_site_id(obj))) not in absence:
                # logging.debug(f"{site_id}-{type(site_id)}")
                # assert site_id in exists | ignore
                continue
            yield obj
    # except:
    #     print('json为空%s\n注意：若连续出现为空提示，请查注意看parse_district方法')

    def update_generator(self, crawler_session: CrawlerSession, fields=None):
        if fields == None:
            fields = (
                "id",
                "site_id",
                "site_url",
            )

        now = datetime.now()

        for cond in self.policy["UPDATE"]["OUT_OF_DATE"]:
            params = {
                "out_of_date": cond["DIFF"],
            }
            if cond["FILTER"] == "Before":
                params["status"] = "todo"
                # params["start__lte"] = str(now + timedelta(hours=3))

            elif cond["FILTER"] == "During":
                params["status"] = "doing"
                # params["start__gte"] = str(now + timedelta(hours=3))
                # params["end__lte"] = str(now - timedelta(hours=3))

            yield from self.fetch_data(crawler_session, params, fields)
