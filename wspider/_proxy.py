
# -*- coding: utf-8 -*-

import time
import random
from random import choice
import requests
from bs4 import BeautifulSoup
import urllib


class Proxy(object):
    def __init__(self, protocol='http'):
        self.protocol = protocol
        self.client = requests.session()

    # 检测一个代理是否可用
    def check_proxy(self, proxy):
        page_url = 'http://1212.ip138.com/ic.asp'
        proxies = {'http': proxy}

        ip = proxy.split('@')[-1].split(':')[0]

        try:
            res = self.client.get(page_url, proxies=proxies)
            time.sleep(1)
        except Exception as e:
            return False

        try:
            if ip in res.content:
                return True
        except:
            soup = BeautifulSoup(res.content, 'html.parser', from_encoding='gbl8030')
            try:
                res_sub = soup.select('center')[0].get_text()
            except:
                return False
            if ip in res_sub:
                return True
        return False

    def get_proxies3(self):
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
        # data = 'username=abcdft123&password=abcdft123%40365935&submit=++%C8%B7+%B6%A8++'
        res = self.client.post(url, data=data, headers=headers)
        html = res.content.decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
        s = soup.select('pre')[0].get_text()
        ps = s.split('\r\n')
        for line in ps:
            ip, port, user, pwd = [val.strip() for val in line.split(':')]
            proxy = {'http': 'http://%s:%s@%s:%s' % (user, pwd, ip, port),
                     'https': 'https://%s:%s@%s:%s' % (user, pwd, ip, port)}
            proxies.append(proxy)
        return proxies


if __name__ == '__main__':
    proxy = Proxy()
    p2 = proxy.get_proxies3()
    for i in p2:
        print i



