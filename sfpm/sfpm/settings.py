# -*- coding: utf-8 -*-
import logging
import os

from rich.logging import RichHandler
from scrapy.utils.log import configure_logging

# Scrapy settings for sfpm project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'sfpm'

SPIDER_MODULES = ['sfpm.spiders']
NEWSPIDER_MODULE = 'sfpm.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'sfpm (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    'sfpm.middlewares.RandomProxyMiddleware': 100,
    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 110,
    # "sfpm.middlewares.SeleniumMiddlewareForChrome": 800,
}
# Retry many times since proxies often fail
RETRY_TIMES = 3
# Retry on most error codes since proxies fail for different reasons
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]

# 代理列表
PROXY_LIST = "/history_crawler/sfpm/proxies.txt"

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'sfpm.middlewares.SfpmDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "sfpm.pipelines.AmapGeoPipeline": 280,
    "sfpm.pipelines.DataExtractPipeline": 290,
    "sfpm.pipelines.SfpmPipeline": 300,
}
# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
# json output encoding
FEED_EXPORT_ENCODING = "utf-8"

# logging
# LOG_LEVEL = "DEBUG"  # default
LOG_LEVEL = "INFO"
# LOG_LEVEL = "WARNING"
LOGSTATS_INTERVAL = 120.0
LOG_FORMAT = "%(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"
LOG_ENABLED = False

configure_logging(install_root_handler=False)

formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATEFORMAT)

handler = RichHandler()
handler.setFormatter(formatter)
handler.setLevel(LOG_LEVEL)

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
logger.addHandler(handler)


# SELENIUM
SELENIUM_DRIVER_NAME = "chrome"
# SELENIUM_DRIVER_EXECUTABLE_PATH = (
#     "/Users/filwaline/Documents/Auction_crawler/chromedriver"
# )
# SELENIUM_DRIVER_EXECUTABLE_PATH = "http://127.0.0.1:4444/wd/hub"
SELENIUM_DRIVER_EXECUTABLE_PATH = "http://selenium_chrome:4444/wd/hub"
SELENIUM_DRIVER_ARGUMENTS = [
    "--headless",
    "--disable-gpu",
    "blink-settings=imagesEnabled=false",
]

