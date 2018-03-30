# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function
import sys
sys.path.append("/niub/www/sourcecode/online-dev-industryspider-deploy/WeChatPublic")

from wspider import core
import xlrd

if __name__ == '__main__':

    # logging.basicConfig(level=logging.DEBUG,
    #                     format='[%(levelname).1s %(asctime)s  %(filename)s:%(lineno)s] %(message)s')
    # logging.getLogger('urllib3').setLevel(logging.ERROR)
    data = xlrd.open_workbook('/niub/www/sourcecode/online-dev-industryspider-deploy/WeChatPublic/wechat.xlsx')
    table = data.sheet_by_name('Sheet1')
    # query = '收视中国'
    # query = '199IT互联网数据中心'
    # query = '未名宏观研究'
    # query = '可来Kline'
    app = core.wechat()
    # app.create_abfile(query)
    # app.run(query)
    for i in table.col_values(0, 2,80 ):
        try:
            app.create_abfile(i)
            app.run(i)
	   

        except:
            pass
