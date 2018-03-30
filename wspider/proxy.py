# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import requests
import time
from random import choice
from bs4 import BeautifulSoup


class ProxyHelper(object):
    def __init__(self):
        self.client = requests.session()

    def get_proxies(self):
        proxies = []
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Host': 'nc-11.f3322.net:1022',
            'Referer': 'http://nc-11.f3322.net:1022/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'
        }
        url = 'http://nc-11.f3322.net:1022/login.php'
        data = {
            'username': 'abcdft123',
            'password': 'abcdft123@920928',
            'submit': '++确+定++'
        }
        try:
            # data = 'username=abcdft123&password=abcdft123%40365935&submit=++%C8%B7+%B6%A8++'
            res = self.client.post(url, data=data, headers=headers)
            html = res.content.decode('utf8')
            soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
            s = soup.select('pre')[0].get_text()
            ps = s.split('\r\n')
            for line in ps:
                ip, port, user, pwd = [val.strip() for val in line.split(':')]
                proxy = {'http': 'http://%s:%s@%s:%s' % (user, pwd, ip, port),
                         'https': 'https://%s:%s@%s:%s' % (user, pwd, ip, port)}
                proxies.append(proxy)
            return proxies
        except:
            return []


def get_proxy():
    return choice(ProxyHelper().get_proxies())


if __name__ == '__main__':
    url = 'http://www.cninfo.com.cn/finalpage/2005-12-01/16252772.PDF'
    resp = requests.get(url, proxies=get_proxy())
    print(resp.text)
    print(get_proxy())
    # print(resp.headers['Content-Type'])
