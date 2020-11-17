#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/11/5 15:41
# @Author  : LiuJiang
# @File    : min.py
# @Software: PyCharm
from scrapy.cmdline import execute
import os
import sys

if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # execute(['scrapy', 'crawl', 'JDOriginal', '--nolog'])
    # execute(['scrapy', 'crawl', 'JDOriginal'])
    # execute(['scrapy', 'crawl', 'taobao', '--nolog'])
    # execute(['scrapy', 'crawl', 'taobaoOriginal', '--nolog'])
    # 当我们重新执行命令：scrapy crawl cnblogs -s JOBDIR=zant/001  时爬虫会根据p0文件从停止的地方开始继续爬取。
    # execute(['scrapy', 'crawl', 'taobaoOriginal', '-s','JOBDIR=zant/001']) # 保存记录启动
    execute(['scrapy', 'crawl', 'taobaoOriginal'])
