# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import os
import requests
import hashlib
import sys
import config
import re
import datetime
from tempfile import NamedTemporaryFile
from reportlab.lib.pagesizes import A4, portrait
from reportlab.pdfgen import canvas
from PIL import Image
import warnings
import uuid
import time

from wspider.http_proxy import get_proxy

def get_image_size(f):
    """获得图片的宽高"""
    return Image.open(f).size


def convert_images_to_pdf(imgs_path, pdf_path):
    """将本地图片变为pdf文件

    每张图片作为单独的一页，大小等比变换到同A4纸同宽"""
    num = 0
    a4w, a4h = portrait(A4)
    c = canvas.Canvas(pdf_path)
    for img in imgs_path:
        w, h = get_image_size(img)
        if w < config.IMAGE_FILTER_WEIGHT or h < config.IMAGE_FILTER_HEIGHT:
            continue
        rw, rh = a4w, h * a4w / w

        c.setPageSize((rw, rh))
        c.drawImage(img, 0, 0, rw, rh)
        c.showPage()
        num = num + 1
    c.save()
    return num

def download2pdf(urls, pdf_path):
    """将图片的链接保存至本地pdf文件"""
    fs = []
    imgs = []
    try:
        for url in urls:
            f = NamedTemporaryFile(delete=False)
            fs.append(f)
            try:
                content = download_img(url)
            except requests.RequestException:
                continue
            if config.ABP and isab(content):
                continue
            f.write(content)

            imgs.append(f.name)
            f.close()
        num = convert_images_to_pdf(imgs, pdf_path)
    except Exception as a:
	print(a)
    finally:
        for f in fs:
            f.close()
            os.remove(f.name)
        try:
            return num
        except UnboundLocalError:
            return 0


def download_img(url):
    for i in range(6):
        try:
            resp = requests.get(url,proxies=get_proxy())
            return resp.content
        except Exception as e:
            print(e)


def isab(content):
    """返回是否为广告图片"""
    data = []
    for x in os.listdir('abp'):
        path = os.path.join('abp', x)

        with open(path, 'r') as f:
            data.extend(f.read().split('\n'))
    return _md5(content) in data


def _md5(content):
    return hashlib.md5(content).hexdigest()


def validate_title(title):
    """处理文件命名非法问题"""
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title


def standardized_item(item):
    rst = dict(item,
               file_type=u".pdf",
               markettype=1,
               market='一级市场',
               payment_type='免费',
               downloaded=True,
               digest='手动编辑',
               publish='wechat',
               )
    timestamp = rst['time']
    # 转换时间格式
    t = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(timestamp))
    rst['time']=datetime.datetime.strptime("%Y-%m-%d %H:%M:%S",t)
#page_num,summary,file_name,file_size,source
    must = {'market', 'file_url', 'markettype', 'oss_path',   'source',
            'downloaded', 'title', 'payment_type',  'digest', 'content',
            'file_type', 'publish'}
    optional = {'time', 'file_size', 'report_title', 'page_num', 'summary', 'file_name',}
    reserved = {'report_category', 'file_time', 'author', 'sitename', 'file_path',
                'source_url', 'report_id', 'dev_mail'}
    auto = {'create_time', 'update_time'}
    # TODO: src_id 未处理
    error_msg = ''
    for key, value in rst.iteritems():
        if key in must:
            error_msg += '' if value else 'standar dization id failed! item must have "{0}".\n'.format(key)
        elif key in reserved:
            error_msg += 'standardization id failed! item["{0}"] is reserved.'.format(key) if value else ''
        elif key in auto:
            warnings.warn('''item's "{}" argument deprecated. pyspider can auto append'''.format(key),
                          DeprecationWarning)
        elif key not in optional:
            error_msg = 'standardization id failed! item can not have "{0}". -> "{0}": {1}'.format(key, value)
    if error_msg:
        raise ValueError(error_msg)

    for key in [x for x in optional | reserved if x not in rst]:
        rst[key] = ''

    if not set(must).issubset(set(rst.keys())):
        raise ValueError('standardization id failed! ({}) not be setted.'
                         .format(' '.join(must - set(rst.keys()))))
    return rst


def get_oss_path(file_url):

    return '{}.pdf'.format(
         uuid.uuid3(uuid.NAMESPACE_DNS, u'{}_{}'.format('wechat_tool', file_url).encode('utf-8')))

if __name__ == '__main__':
    pass
