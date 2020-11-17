# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from typing import List, Optional
from scrapy import signals, Spider, Request
from scrapy.crawler import Crawler

class SfpmSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class SfpmDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomProxyMiddleware:
    """用于给请求添加代理的中间件"""

    def __init__(self, proxy_list: List[str]):
        if len(proxy_list) == 0:
            raise ValueError('代理 IP 列表长度为 0')

        self.__proxy_list = proxy_list  # 代理 IP 列表
        self.__index = 0

    @property
    def proxy_url(self) -> str:
        """从代理列表中循环选择一个代理"""
        proxy = self.__proxy_list[self.__index]
        self.__index = (self.__index + 1) % len(self.__proxy_list)
        return proxy

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        """拉取芝麻代理 IP 地址"""
        proxy_list_path: Optional[str] = crawler.settings.get('PROXY_LIST', None)

        if proxy_list_path is None:
            raise ValueError('未配置代理 IP 的地址')

        with open(proxy_list_path) as file:
            return cls(file.readlines())

    def process_request(self, request: Request, spider: Spider):
        if 'sf.taobao.com/item_list.htm' in request.url:  # 爬取新的淘宝数据时才使用代理 IP
            request.meta['proxy'] = self.proxy_url
