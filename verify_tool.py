#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""1.返回不同的collection的数据不同类型的数据，是否正常的存在阿里云，以及数据是否符合存储规范。
•	文件类型是否与存储在数据库中的类型是否一致(文件类型两方面判断headers和https://pypi.python.org/pypi/python-magic/模块，后者判断会更准确，因为阿里云的headers是爬虫开发者自定义的)
•	必填项（oss_path, file_type, page_num, create_time, update_time, file_name, market, sitename, source, source_url, downloaded, file_url, payment_type, dev_mail）是否都有填写
•	file_type类型在html, pdf, doc, docx, excel, ppt(后期可能会有添加)等常见格式中
•	page_num是否存在非数字类型， 可以为负数，None ,不允许存在字符串
•	create_time，update_time为日期格式
•	downloaded布尔型
"""
import sys
import json
import math
import time
import magic
import click
import logging
import pymongo
import requests

from time import sleep
from urlparse import urljoin
from datetime import datetime, timedelta
from pprint import pprint as p, pformat

MUST = {'file_type', 'org_id', 'create_time', 'update_time', 'time', 'file_size', 'src_id', 'title', 'type', 'plate',
        'storage', 'timestamp', 'stock_code', 'stock_name', 'file_url', 'column', 'oss_path', 'export_flag',
        'export_version', 'category_id', 'downloaded', 'source_url'}
FILE_TYPE = [".html", ".shtml", ".jhtml", ".pdf", ".doc", ".docx", ".xlsx", ".pptx", ".xls", ".ppt"]
FILE_MIME_TYPE = ['application/pdf',
                  'application/msword',
                  # Fix:  mime type of '.doxc' maybe is application/zip.
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                  'application/vnd.ms-excel',
                  'application/vnd.ms-powerpoint',
                  'text/html',
                  'application/x-gzip',  # 压缩过的html
                  'application/zip',
                  "CDF V2 Document, corrupt: Can't read SAT",
                  "CDF V2 Document, corrupt: Can't read SSAT"
                  'application/octet-stream',
                  'text/rtf']


def verify(item):
    # assert MUST.issubset(set(item.keys())), u'缺少必填项'
    for key in MUST:
        assert item.has_key(key), u'必填项 {} 未填! value: <{}>'.format(key, item[key])
    assert item['file_type'] in FILE_TYPE, u'file_type: {}'.format(item['file_type'])  # '.' is ok
    # assert isinstance(item['page_num'], int) or (not item['page_num']), u'page_num: {}'.format(item['page_num'])
    assert isinstance(item['file_size'], int), u'file_size: {}'.format(item['file_size'])
    assert isinstance(item['src_id'], (unicode, str)) and len(item['src_id']) <= 30, u'src_id: {}'.format(
        item['src_id'])
    assert item['storage'] == 'oss', u'storage: {}'.format(item['storage'])
    assert isinstance(item['create_time'], datetime), u"create_time: {}".format(item['create_time'])
    assert isinstance(item['update_time'], datetime), u"update_time: {}".format(item['update_time'])
    assert isinstance(item['time'], datetime), u"update_time: {}".format(item['update_time'])
    assert isinstance(item['downloaded'], bool), u"downloaded: {}".format(item['downloaded'])
    assert isinstance(item['export_flag'], bool), u"export_flag: {}".format(item['export_flag'])
    assert isinstance(item['export_version'], int), u"export_version: {}".format(item['export_version'])
    assert item['downloaded'] is True, u'未下载完成'  # TODO: download is False？
    verify_oss_path(item['oss_path'])


def verify_oss_path(oss_path):
    try:
        with requests.get("http://abc-crawler.oss-cn-hangzhou.aliyuncs.com/{}".format(oss_path), stream=True) as resp:
            mine_type = magic.from_buffer(resp.raw.read(1024), mime=True)
            if oss_path.lower().endswith('.pdf'):
                assert 'pdf' in mine_type.lower(), 'mine_type: {} oss_path: {}'.format(mine_type, oss_path)
            elif "htm" in oss_path.lower().split(".")[-1]:
                pass
            elif oss_path.lower().endswith('.docx') or oss_path.lower().endswith('.doc'):
                assert mine_type in [
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/zip',
                    'text/rtf',
                    "CDF V2 Document, corrupt: Can't read SAT",
                    "CDF V2 Document, corrupt: Can't read SSAT",
                    "application/octet-stream"
                ], 'mine_type: {} oss_path: {}'.format(mine_type, oss_path)
            elif oss_path.lower().endswith('.xlsx') or oss_path.lower().endswith('.xls'):
                assert mine_type in ['application/vnd.ms-excel'], 'mine_type: {} oss_path: {}'.format(mine_type,
                                                                                                      oss_path)
            elif oss_path.lower().endswith('.pptx') or oss_path.lower().endswith('.ppt'):
                assert mine_type in ['application/vnd.ms-powerpoint'], 'mine_type: {} oss_path: {}'.format(mine_type,
                                                                                                           oss_path)
            else:
                pass
        assert mine_type in FILE_MIME_TYPE, 'mine_type: {} oss_path: {}'.format(mine_type, oss_path)
    except requests.exceptions.RequestException as e:
        raise AssertionError(u'http request failed! -> {}'.format(e.message))


def get_email(col):
    """尝试从 collection 中找到开发者邮箱"""
    try:
        return next(col.find({}))[u'dev_mail'].lower().strip()
    except (StopIteration, KeyError, AttributeError):
        return None


def core(save_type, result_db, ignore, verify_func=lambda x: x, output=None, filter_email=None):
    db = get_db(result_db)
    projects = filter(verify_func, db.collection_names())
    projects = set(projects) - set(ignore)

    if filter_email:
        filter_email = set(x.lower() for x in filter_email)
        projects = filter(lambda col: get_email(db[col]) in filter_email, projects)

    logging.info(u'read over. total: {} {}'.format(len(projects), pformat(projects)))
    sys.stdout.write(u'total: {}\n'.format(len(projects)))
    output.write(u"{:<25}{:10}{:10}{:10}\n".format('name', 'failed', 'seccess', 'total'))

    for index, project in enumerate(projects):
        logging.info(u'handle {}'.format(project))

        success, failed = 0, 0
        _len = db[project].count()
        for item in db[project].find({}):
            try:
                verify(item)
                success += 1
            except AssertionError as e:

                failed += 1
                logging.info(u'[{} faild!] _id({}): {} '.format(project, item['_id'], e.message))

            sys.stdout.write(u'\r{:<3} {:20} {:4}/{:<4}: [{:40}] failed: {} ({:>6.2f}%).'
                             .format(index + 1,
                                     project,
                                     success + failed,
                                     _len,
                                     '#' * int(math.ceil((success + failed) * 40.0 / _len)),
                                     failed,
                                     failed * 100.0 / _len))

        sys.stdout.write('\n')
        output.write(u'{:<25}{:<10}{:<10}{:<10}\n'.format(project, failed, success, success + failed))


@click.command()
@click.option('--save-type', default='text', type=click.Choice(['text', 'json']), help=u"输出结果的类型")
@click.option('--ignore', '-i', multiple=True, default=["tomson_pdf_list",
                                                        "industry.report.kpmg",
                                                        "industry.report.imf",
                                                        "industry.report.pichbook"],
              help=u'需要忽略的project')
@click.option('--ignore-file', type=click.File('rb'), help=u"需要忽略的project的列表文件")
@click.option('--output', '-o', default='output.txt', type=click.File('wb'), help=u'输出到文件')
@click.option('--filter-email', '-e', multiple=True, help=u'通过dev email筛选')
@click.option('--result-db', '-r',
              default='mongodb://spider2:ThE_eJedRE5a@114.55.39.144:3717/original_data?replicaSet=mgset-3255385',
              help=u'指定查看数据库')
@click.argument('projects', nargs=-1)
def main(save_type, ignore, result_db, output, filter_email, ignore_file, projects):
    print('----------------config--------------')
    p(locals())
    print('(>.<)')
    print('------------------------------------')

    if ignore_file:
        ignore = list(filter(lambda x: x, (l.strip().lower() for l in ignore_file.readlines()))) + list(ignore or [])

    if not projects:
        verify_func = lambda x: x.startswith(u'industry_')
    else:
        projects = list([x.lower() for x in projects])
        verify_func = lambda x: x.lower() in projects

    core(save_type, result_db, ignore,
         verify_func=verify_func,
         output=output,
         filter_email=filter_email)


def get_db(link):
    logging.info('get_db: {}'.format(link))
    try:
        return pymongo.MongoClient(link).get_database()
    except pymongo.errors.ConfigurationError:
        logging.info('get_db faild!')
        print(u'resultdb: "{}" 是无效的!\nexit...'.format(link))
        sys.exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename='logging.out', filemode='a')
    main()
