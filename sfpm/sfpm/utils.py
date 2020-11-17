#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/11/16 15:17
# @Author  : LiuJiang
# @File    : utils.py
# @Software: PyCharm
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Tuple, Union
from urllib.parse import quote

import pandas as pd
from bs4 import BeautifulSoup
from scrapy.http import HtmlResponse
from scrapy.selector import Selector, SelectorList
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .console import console

# logging.config.dictConfig({
#     "version":1,
#     "disable_exist_loggers": True
# })


class RebuildTable:

    #     template = """
    # <html>
    #     <head>
    #         <meta charset="utf-8">
    #         <style>@media screen and (max-width:1280px){.rwdtable{border:0}.rwdtable caption{font-size:1.3em}.rwdtable thead{border:0;clip:rect(0 0 0 0);height:1px;margin:-1px;overflow:hidden;padding:0;position:absolute;width:1px}.rwdtable tr{background-color:lightgrey;border-bottom:3px solid #ddd;display:block;margin-bottom:.625em}.rwdtable td{color:#d20b2a;border-bottom:1px solid #ddd;display:block;font-size:1.2em;text-align:center}.rwdtable td:before{color:black;content:attr(data-label);float:left;font-weight:bold;font-size:1.3em;text-transform:uppercase}.rwdtable td:last-child{border-bottom:0}}</style>
    #     </head>
    #     <body>
    #         <table class="rwdtable"></table>
    #     </body>
    # </html>
    # """

    # @classmethod
    # def build(cls, html: str) -> str:
    #     soup = BeautifulSoup(html, "lxml")
    #     if not soup.table:
    #         return html
    #     for tag in list(soup.body.descendants):
    #         if tag.name == "table":
    #             table = cls.__tableFromDict(
    #                 dict(list(cls.__kvFromDataFrame(cls.__dataFrameFromHtml(str(tag)))))
    #             )
    #             parent = tag.parent
    #             index = parent.index(tag)
    #             parent.contents[index].replace_with(table.table)

    #     _soup = BeautifulSoup(cls.template, "lxml")
    #     _soup.body.replace_with(soup.body)
    #     return f"{_soup}"

    @classmethod
    def build_inline(cls, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")

        if not soup.table:
            return html

        for tag in list(soup.body.descendants):
            if tag.name == "table":
                try:
                    table = cls.__tableInlineStyleFromDict(
                        dict(
                            list(
                                cls.__kvFromDataFrame(cls.__dataFrameFromHtml(str(tag)))
                            )
                        )
                    )
                except ValueError as e:
                    # table cannot be parse
                    logging.error(e)
                    continue
                except AttributeError as e:
                    # assigned non-str value to Tag.string
                    logging.error(e)
                    continue
                except IndexError as e:
                    # pandas.read_html return empty list
                    logging.error(e)
                    continue
                else:
                    parent = tag.parent
                    index = parent.index(tag)
                    parent.contents[index].replace_with(table.table)

        if (div := soup.find("div", attrs={"id": "rebuild"})) :
            return str(div)

        # replace <html><body>...</body></html> as <div id='rebuild'>...</div>
        soup.body.wrap(soup.new_tag("div", **{"id": "rebuild"}))
        soup.body.unwrap()
        return str(soup.div.extract())

    @classmethod
    def __dataFrameFromHtml(cls, table: str) -> pd.DataFrame:
        df = pd.read_html(table)[0]
        return df.dropna()

    @classmethod
    def __kvFromDataFrame(cls, df: pd.DataFrame):
        for i, row in df.iterrows():
            _list = [row[0]]
            for value in row[1:]:
                if _list[-1] == value:
                    continue
                _list.append(value)

            if len(_list) == 1:
                _list.insert(0, "")

            if len(_list) % 2 == 1:
                _list.pop(0)

            for i in range(0, len(_list), 2):
                yield _list[i], _list[i + 1]

    # @classmethod
    # def __tableFromDict(cls, data: dict):
    #     soup = BeautifulSoup('<table class="rwdtable"></table>', "lxml")

    #     _tr_th = soup.new_tag("tr")
    #     _tr_td = soup.new_tag("tr")

    #     for key, value in data.items():

    #         _th = soup.new_tag("th")
    #         _th.string = key

    #         _td = soup.new_tag("td", **{"data-label": key})
    #         _td.string = value

    #         _tr_th.append(_th)
    #         _tr_td.append(_td)

    #     thead = soup.new_tag("thead")
    #     thead.append(_tr_th)
    #     tbody = soup.new_tag("tbody")
    #     tbody.append(_tr_td)
    #     soup.body.table.append(thead)
    #     soup.body.table.append(tbody)
    #     return soup

    @classmethod
    def __tableInlineStyleFromDict(cls, data: dict):

        soup = BeautifulSoup("<table></table>", "lxml")

        for key, value in data.items():

            tr = soup.new_tag(
                "tr",
                style="background-color:lightgrey;border-bottom:3px solid #ddd;display:block;",
            )

            td_key = soup.new_tag(
                "td",
                style="color:black;float:left;font-weight:bold;font-size:1.3em;text-transform:uppercase;",
            )
            td_key.string = str(key)
            tr.append(td_key)

            td_val = soup.new_tag(
                "td",
                style="color:#d20b2a;border-bottom:1px solid #ddd;display:block;font-size:1.2em;text-align:center;",
            )
            td_val.string = str(value)
            tr.append(td_val)

            soup.table.append(tr)

        return soup


class ParseHelper:

    rmb_symbol = "[\¥\￥]"  # b'\xc2\xa5', b'\xef\xbf\xa5'
    word_pattern = "[^\W\d]"  # match any alphanumeric but not digit
    number_pattern = "[0-9]*\.[0-9]+|[0-9]+\.?"

    money_unit_pattern = (
        f"(?:{rmb_symbol}(?P<UNIT_1>{number_pattern})(?![万千仟]元))?"
        f"(?:(?P<unit_1>{number_pattern})元)?"
        f"(?:{rmb_symbol}?(?P<unit_1000>{number_pattern})[千仟]元)?"
        f"(?:{rmb_symbol}?(?P<unit_10000>{number_pattern})万元)?"
    )
    price_pattern_mapping = {
        "price_initial": re.compile(
            f"(起拍|起始|变卖)(?!保证)({word_pattern}{{,6}}){money_unit_pattern}"
        ),
        "price_current": re.compile(
            f"(当前|成交)({word_pattern}{{,6}}){money_unit_pattern}"
        ),
        "price_consult": re.compile(
            f"(评估|市场)({word_pattern}{{,6}}){money_unit_pattern}"
        ),
        "price_margin": re.compile(f"(保证)({word_pattern}{{,6}}){money_unit_pattern}"),
        "price_step": re.compile(f"(加价|增价)({word_pattern}{{,6}}){money_unit_pattern}"),
    }

    area_unit_pattern = f"((?P<size>{number_pattern})(平方米|㎡|m2))"
    area_pattern_mapping = {
        "area_building": re.compile(
            f"(建筑面积|建面|总面积)({word_pattern}{{,5}}){area_unit_pattern}"
        ),
        "area_saleable": re.compile(
            f"(使用|实用|销售|套内|使用权)面积({word_pattern}{{,5}}){area_unit_pattern}"
        ),
    }

    date_pattern = (
        "(?:(?P<{prefix}year>[0-9]{{2,4}})年)?"
        "(?:(?P<{prefix}month>[0-9]{{1,2}})月)?"
        "(?P<{prefix}day>[0-9]{{1,2}})日"
        "(?:(?P<{prefix}midday>上午|下午|)(?P<{prefix}hour>[0-9]{{1,4}})时?)?"
    )
    start_end_date_pattern = re.compile(
        # prefix r just for align
        f"({word_pattern}{{,4}})"
        f"{date_pattern.format(prefix='start_')}"
        f"({word_pattern}{{,3}})"
        f"{date_pattern.format(prefix='end_')}"
        r"(\w{,8}?)(?=延时)"
    )

    cleaned_pattern = f"[\w\.\-\㎡\/{rmb_symbol[1:-1]}]+"

    @classmethod
    def bulk_parse_price(
        cls,
        cleaned_text: Union[str, List[str]],
        key_mapping: Union[str, List[str], Dict[str, int]] = "__all__",
        scale: int = 1,
        default=0,
        epsilon=1,
    ) -> Dict[str, int]:

        if isinstance(cleaned_text, list):
            cleaned_text = "".join(cleaned_text)

        if key_mapping == "__all__":
            key_mapping = {key: scale for key in cls.price_pattern_mapping.keys()}
        elif isinstance(key_mapping, str):
            key_mapping = {key_mapping: scale}
        elif isinstance(key_mapping, list):
            key_mapping = {key: scale for key in key_mapping}

        return {
            key: cls.get_best_value(
                key=key,
                results=cls.compute_prices(
                    price_pattern=cls.price_pattern_mapping[key],
                    cleaned_text=cleaned_text,
                    scale=scale,
                ),
                default=default,
                epsilon=epsilon,
            )
            for key, scale in key_mapping.items()
        }

    @classmethod
    def compute_prices(
        cls, price_pattern: re.Pattern, cleaned_text: str, scale: int = 1
    ) -> List[int]:
        return [
            int(val)
            for result in price_pattern.finditer(cleaned_text)
            if (
                val := sum(
                    float(v) * int(k[5:]) * scale
                    for k, v in result.groupdict().items()
                    if v != None
                )
            )
            > 0
        ]

    @classmethod
    def get_best_value(
        cls,
        key: str,
        results: List[int],
        default: int = 0,
        epsilon=1,
        short_circuit=None,
    ) -> int:
        if results:
            mean = sum(results) / len(results)

            # [(origin, squared_error)...]
            results_augmented = [(p, (p - mean) ** 2) for p in results]

            mse = sum(ra[1] for ra in results_augmented) / len(results)
            if mse > epsilon:
                logging.warning(f"{key}-{results}: MSE={mse} > eps={epsilon}")
                if callable(short_circuit):
                    val = short_circuit(results)
                    logging.warning(
                        f"Apply short-circuit: return {val} # {short_circuit.__name__}({results})"
                    )
                    return val

            best = min(results_augmented, key=lambda ra: ra[1])
            logging.debug(
                f"Get the best {key} has value={best[0]} with minimum squared_error={best[1]}"
            )
            return best[0]

        logging.debug(f"Empty results for {key}, return {default=}")
        return default

    @classmethod
    def get_cleaned_text(
        cls,
        source: Union[str, Selector, SelectorList],
        sep: str = "",
        cleaned_pattern: str = None,
    ) -> Union[list, str]:

        if cleaned_pattern == None:
            cleaned_pattern = cls.cleaned_pattern

        if isinstance(source, str):
            selector = Selector(text=source)
        else:
            # Response, Selector, SelectorList
            selector = source

        # source 可能会出现 None 的情况，导致 selector 也为 None，这里做排除
        try:
            _list = selector.xpath(".//text()").re(cleaned_pattern)
        except AttributeError:
            return ''

        if sep != None:
            return sep.join(_list)
        return _list

    @classmethod
    def get_html(
        cls, source: Union[str, Selector, SelectorList], sep: str = "\n",
    ) -> Union[list, str]:

        if isinstance(source, str):
            selector = Selector(text=source)
        else:
            # Response, Selector, SelectorList
            selector = source

        _list = selector.getall()

        if sep != None:
            return sep.join(_list)
        return _list

    @classmethod
    def bulk_parse_area(
        cls,
        cleaned_text: Union[str, List[str]],
        key_list: Union[str, List[str]] = "__all__",
        default=0,
        epsilon=1,
    ) -> Dict[str, float]:

        if isinstance(cleaned_text, list):
            cleaned_text = "!@#$%^&*".join(cleaned_text)

        if key_list == "__all__":
            key_list = list(cls.area_pattern_mapping.keys())
        elif isinstance(key_list, str):
            key_list = [key_list]

        return {
            key: cls.get_best_value(
                key=key,
                results=cls.compute_areas(
                    area_pattern=cls.area_pattern_mapping[key],
                    cleaned_text=cleaned_text,
                ),
                default=default,
                epsilon=epsilon,
                short_circuit=max,
            )
            for key in key_list
        }

    @classmethod
    def compute_areas(cls, area_pattern: re.Pattern, cleaned_text: str) -> List[float]:
        return [
            float(result.group("size"))
            for result in area_pattern.finditer(cleaned_text)
        ]

    @classmethod
    def parse_start_end_date(
        cls, cleaned_text: Union[str, List[str]],
    ) -> Tuple[datetime]:
        if isinstance(cleaned_text, list):
            cleaned_text = "".join(cleaned_text)

        if (result := cls.start_end_date_pattern.search(cleaned_text)) :
            start = cls.compute_datetime(
                result.groupdict(),
                "start_",
                year_default=(now := datetime.now()).year,
                month_default=now.month,
            )
            end = cls.compute_datetime(
                result.groupdict(),
                "end_",
                year_default=start.year,
                month_default=start.month,
            )

            logging.debug(f"{start=}, {end=}")
            assert start < end

            return start, end

        logging.warning("Fail to parse start and end.")
        return None, None

    @classmethod
    def compute_datetime(
        cls,
        result: Dict[str, str],
        prefix: str,
        year_default: int = None,
        month_default: int = None,
    ) -> datetime:
        _prefix = {
            k[len(prefix) :]: v
            for k, v in result.items()
            if k.startswith(prefix)
            if bool(v)
        }
        _prefix.setdefault("year", year_default)
        _prefix.setdefault("month", month_default)

        _midday = _prefix.pop("midday", "")
        _prefix = {k: int(v) for k, v in _prefix.items()}

        if _prefix["hour"] >= 100:  # while matching [0-9]{3,4}, e.g. '1000' '830'
            _prefix["minute"] = (_prefix["hour"] % 100) % 60
            _prefix["hour"] //= 100

        if _midday == "下午":
            _prefix["hour"] += 12

        return datetime(**_prefix)

    @classmethod
    def index_of_sibling_nodes(cls, selector: Selector) -> int:
        # nodes indexing 0-base
        return int(float(selector.xpath("count(./preceding-sibling::*)").get()))

    @classmethod
    def slice_of_sibling_nodes(
        cls, selector: Selector, start: int, end: int
    ) -> List[Selector]:
        # start, end indexing 0-base
        # position() indexing 1-base
        # plus 1 indeed
        return selector.xpath(
            f"../child::*[position() >= {start + 1} and position() < {end + 1}]"
        )

    @classmethod
    def preprogress_jsdata(cls, text: str):
        if not text:
            return {}

        # replace single quote ' to double quote "
        _text = re.sub(r"'", r'"', text)

        # put double quote "" around key
        _text = re.sub(r"(\w+):(?=\s*\")", r'"\1":', _text)

        # remove useless outer ()
        _text = re.sub(r"\((.+)\)", r"\1", _text)

        try:
            logging.debug(_text)
            return json.loads(_text)
        except:
            console.print_exception()
            return {}

    @classmethod
    def to_bytes(cls, data: Union[list, dict]):
        result = []
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    result.append(f"{k}={v}")
                else:
                    _v = str(v).replace(" ", "")
                    result.append(f"{k}={_v}")

        data_str = "&".join(result).replace("'", '"')
        return quote(data_str).encode()


class SeleniumHelper:
    @classmethod
    def page_has_loaded(cls, driver):
        logging.debug("Checking if {} page is loaded.".format(driver.current_url))
        page_state = driver.execute_script("return document.readyState;")
        return page_state == "complete"

    @classmethod
    def update_response(cls, response):
        driver = response.meta["driver"]
        request = response.request
        request.meta.update({"driver": driver})

        return HtmlResponse(
            driver.current_url,
            body=str.encode(driver.page_source),
            encoding="utf-8",
            request=request,
        )

    @classmethod
    def click(cls, response, locator, value):
        element = WebDriverWait(response.meta["driver"], 10).until(
            EC.element_to_be_clickable((locator, value))
        )
        element.click()
        return cls.update_response(response)

    @classmethod
    def exist(cls, response, locator, value):
        try:
            element = WebDriverWait(response.meta["driver"], 3).until(
                EC.presence_of_element_located((locator, value))
            )
            return True
        except:
            console.print_exception()
            return False

