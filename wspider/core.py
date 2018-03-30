# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import os
import re
import io
import json
# import pdfkit   #将整个网页转化为pdf包
import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup
from lxml import etree
from urlparse import urljoin
from PIL import Image
from pprint import pformat
from pymongo import MongoClient
from wspider.http_proxy import get_proxy

from wspider.tools import download_img, download2pdf, _md5
from wspider.tools import validate_title
from wspider.tools import get_oss_path
from wspider.tools import standardized_item
from wspider.upload import uploader
from wspider import log_config
import yanzheng
#import sys
#sys.path.append("")

class wechat():
    def __init__(self):
        self.headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/63.0.3239.132 Safari/537.36 '
        }
        self.log = log_config.createlog('wechat.log', 'wehcat')


    def connectmongo(self):
        client = MongoClient('mongodb://spider2:ThE_eJedRE5a@dds-bp1d09d4b278ceb41.mongodb.rds.aliyuncs.com:3717,dds-bp1d09d4b278ceb42.mongodb.rds.aliyuncs.com:3717/cr_data?replicaSet=mgset-3255385')
        db = client.cr_data
        collection = db['wechat_data']
        return collection


    def run(self, query):
        file_path = os.path.join('files', validate_title(query))
        self.log.debug(validate_title(query))
        if not os.path.exists(file_path):
            os.mkdir(file_path)

        index_url = self.get_index_by_sougou(query)
        rst = self.get_details(index_url)
        if rst == None:
            self.log.warning('此公众号无法爬取：{}'.format(query))
            exit(query+'无法爬取')
        for i in rst:
            url = i['file_url']
            self.log.info('{} total: .{}'.format(query, len(url)))

            title, img_urls, content = self.get_image_msg(url)
            pdf_path = os.path.join('files', '{}{}{}.pdf'.format(validate_title(query), os.sep, validate_title(title)))
            if os.path.exists(pdf_path):
                continue

            file_name = pdf_path.split('/')[-1]
            page_num = download2pdf(img_urls, pdf_path)
	 
            if page_num >= 3:

                oss_path = get_oss_path(url)
                fsize = os.path.getsize(pdf_path)
                i.update({
                    'oss_path': oss_path,
                    'content': content,
                    'page_num': page_num,
                    'file_name': file_name,
                    'file_size': fsize,
                })
                j = standardized_item(i)

                wechat = self.connectmongo()
                wechat.insert(j)
                self.log.info('insert {} succeed'.format(title))
            else:
                continue
            if uploader.upload_file(oss_path,pdf_path):
                self.log.info('upload success\n')







    def get_index_by_sougou(self, query):
        API = "http://weixin.sogou.com/weixin?p=01030402&query={query}&type=2&ie=utf8"
	print(query)
        for i in range(11):
            try:
                resp = requests.get(API.format(query=query), headers=self.headers, proxies=get_proxy())
                break
            except requests.RequestException as e:
                self.log.warning('正在尝试重新爬取~~' + str(e))
        else:
            self.log.warning('无法爬取此页面' + API.format(query=query))
            raise Exception('无法爬取此页面' + API .format(query=query))

        root = etree.HTML(resp.content)
        try:
            rst = root.xpath(r"//p[@class='gzh-name']//a/@href")[0]
            return rst
        except:
            self.log.warning('index page failed: {}'.format(query))
            raise ValueError


    def judge_url(self,content):
        soup = BeautifulSoup(content, 'lxml')
        msg = json.loads(re.search(r'''msgList\s*
                                                  =\s*
                                                  ({.*?})\s*
                                                  ;
                                               ''', content, flags=re.X).group(1))
        rst = []
        wechat = self.connectmongo()
        source = soup.find_all('p', class_='profile_account')[0].get_text()
        for x in msg['list']:
            dic = {}
            dic["file_url"] = urljoin("https://mp.weixin.qq.com/", x['app_msg_ext_info']['content_url']).replace(
                '&amp;', '&')
            dic["source"] = source
            dic["summary"] = x['app_msg_ext_info']["digest"]
            dic["time"] = x['comm_msg_info']["datetime"]
            dic["title"] = x['app_msg_ext_info']["title"]
            list1 = list(wechat.find({'title': dic["title"]}))

            if len(list1) == 0 or dic["file_url"].replace(' ', '') != '':
                rst.append(dic)
            else:

                self.log.info('duplicate report')
            for i in x['app_msg_ext_info']['multi_app_msg_item_list']:
                dic2 = {}
                dic2["file_url"] = urljoin("https://mp.weixin.qq.com/", i['content_url']).replace('&amp;', '&')
                dic2["source"] = source
                dic2["summary"] = i["digest"]
                dic2["title"] = i["title"]
                dic2["time"] = dic["time"]
                list1 = list(wechat.find({'title': dic2["title"]}))

                if len(list1) == 0 and dic2["file_url"].replace(' ', '') != '':
                    rst.append(dic2)
                else:
                    self.log.info('duplicate report')

        return rst


    def get_details(self,url):
	print(url)
        for i in range(6):
            try:
                resp = requests.get(url, headers=self.headers, proxies=get_proxy())
                resp.encoding = 'utf-8'
                break
            except Exception as a:
                self.log.warning('request fail {},try again'.format(a))



        try:
            #取得最近网页里的链接（大json）
            rst = self.judge_url(resp.content)
            return rst
        except:
            self.log.info('need yanzheng')
            cookie = yanzheng.yanzheng(url)
            resp = requests.get(url, headers=self.headers, cookies=cookie, proxies=get_proxy())
            resp.encoding = 'utf-8'
            rst = self.judge_url(resp.content)
            return rst





    def get_image_msg(self,url):
        self.log.info(u'下载成功{}'.format(url))
        for i in range(6):
            try:
                resp = requests.get(url, headers=self.headers, proxies=get_proxy())
                tree = etree.HTML(resp.content)

                title = tree.xpath(r"//*[@id='activity-name']/text()")[0].strip()

                img_urls = tree.xpath(r"//img[@data-src]/@data-src")
                content = resp.content

                return title, img_urls, content
            except requests.RequestException:
                try:
                    self.log.warning('正在尝试重新爬取~~')
                except:
                    self.log.warning('无法爬取此页面' + url)
                    raise Exception('无法爬取此页面' + url)



# def topdf(content):
#     """将html网页转换成pdf
#
#      帮你下载图片， 处理样式表"""
#     # FIX: 请加上代理， 没有代理，怕是要罚款💀
#     logging.debug('topdf: {}'.format(content))
#     f = io.BytesIO(content)
#     path_wkthmltopdf = r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
#     config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
#     pdfkit.from_file(f, 'out.pdf', configuration=config)


    def create_abfile(self, website, show=True):
        """生成一个广告图片的md5的黑名单

        :param website: 公众号名称
        :param show: 是否展示出黑名单图片
        :return:
        """

        index_url = self.get_index_by_sougou(website)
        urls = self.get_details(index_url)

        self.log.warning('crate_abfile: {}'.format(website))
        self.log.warning('{} total: {}'.format(website, len(urls)))

        img_cache = {}
        tmp = set()
        count = {}
        for url in urls:
            link = url["file_url"]
            title, img_urls, content = self.get_image_msg(link)
        
            ab = set()
            for imgu in img_urls:
                try:
                    content = download_img(imgu)
                except requests.RequestException:
                    self.log.warning('无法下载' + link)
                    continue

                m = _md5(content)
                ab.add(m)
                img_cache[m] = content
            for x in tmp & ab:
                if x in count:
                    count[x] += 1
                else:
                    count[x] = 1
            tmp |= ab

        path = os.path.join('abp/', website)
        with open(path, 'w') as f:
            for i in count.keys():
                f.write(i + '\n')
        self.log.info('find ab: {}'.format(pformat(count)))

        if show:
            for x in list(count.keys()):
                img = Image.open(io.BytesIO(img_cache[x]))
                img.show(title=x)


if __name__ == '__main__':
    pass

