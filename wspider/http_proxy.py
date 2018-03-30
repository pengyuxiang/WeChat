# -*- coding: utf-8 -*-

from wspider import _proxy
import logging
import requests
import random
from random import choice
import time


class Response(object):
    def __init__(self):
        self.headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
                        'Connection': 'keep-alive',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.35'}
        self.logger = logging.getLogger('http_requests')
        self.session = requests.session()
        self.proxy = _proxy.Proxy()
        self.proxy_list = self.get_proxy()

    def get_proxy(self):
        try:
            return self.proxy.get_proxies3()
        except Exception as e:
            self.logger.error(u'获取代理失败,error_msg:%s' % e)
            # 返回一个tuple,用于list.choice进行选择
            return None

    def get_response(self, method, url, encoding=None, sleep_time=0, depth=0, use_proxy=True, error_proxy=None, **kwargs):
        """
        当depth < 0用本地ip爬取数据，若depth >= 0用代理ip爬取
        :return:
        """
        depth += 1
        if not url:
            return None

        if ('http://' not in url) and ('https://' not in url):
            return None

        # 若传入参数没有headers,会用默认headers
        if not kwargs.has_key('headers'):
            kwargs['headers'] = self.headers

        # 默认不验证https证书
        if not kwargs.has_key('verify'):
            kwargs['verify'] = False

        # 默认超时为60秒
        if not kwargs.has_key('timeout'):
            kwargs['timeout'] = (10,10)

        # 若use_proxy为False,则不用代理，否则随机取代理列表的代理
        if not use_proxy:
            kwargs['proxies'] = None
        else:
            if self.proxy_list:
                self.logger.debug(u'此时获取代理列表不为空')
                # 移除可能失效的代理
                if error_proxy and error_proxy in self.proxy_list:
                    self.proxy_list.remove(error_proxy)
                if self.proxy_list:
                    kwargs['proxies'] = random.choice(self.proxy_list)
                else:
                    kwargs['proxies'] = None

            else:
                self.logger.info(u'此时获取代理列表为空')
                kwargs['proxies'] = None
                # 若代理有问题，直接重新刷新代理, 如果不刷新代理，可能会导致整个程序的后期都用的本地代理
                self.proxy_list = self.get_proxy()



        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 200:
                if encoding:
                    response.encoding = encoding
                return response
            else:
                self.logger.warning('url:%s, method:%s, kwargs:%s,\
                 status_code:%d' % (url, method, str(kwargs), response.status_code))
                return None
        except requests.exceptions.ProxyError as e:
            self.logger.info('url:%s, method:%s, kwargs:%s, error_msg:%s' % (url, method, str(kwargs),e))
            if depth>3:
                self.logger.info(u'请求递归次数:%d,大于3返回response为None' % depth)
                return None
            # 若代理有问题，直接重新刷新代理
            self.proxy_list = self.get_proxy()
            # 若获得代理为None将会使用本地代理，或者递归层数大于3，跳出递归
            self.logger.info(u'使用代理请求出错,depth:%d,更新代理再次请求' % depth)
            response = self.get_response(method, url, encoding=encoding, sleep_time=sleep_time, error_proxy=kwargs['proxies'], depth=depth, **kwargs)
            if response:
                return response
            else:
                # 代理使用失败，使用本地代理
                self.logger.warning(u'代理出错,将不使用代理访问')
                return self.get_response(method, url, encoding=encoding, sleep_time=sleep_time,use_proxy=False, depth=depth, **kwargs)


        except requests.exceptions.Timeout as e:
            self.logger.warning('url:%s, method:%s, kwargs:%s, error_msg:%s' % (url, method, str(kwargs),e))
            if depth>3:
                self.logger.info(u'请求递归次数:%d,大于3返回response为None' % depth)
                return None

            self.logger.info(u'请求超时出错,depth:%d,再次请求' % depth)
            response = self.get_response(method, url, encoding=encoding, sleep_time=sleep_time, depth=depth, **kwargs)
            if response:
                return response
            else:
                # 代理使用失败，使用本地代理
                self.logger.warning(u'使用代理出错,将不使用代理访问')
                return self.get_response(method, url, encoding=encoding, sleep_time=sleep_time,use_proxy=False, depth=depth, **kwargs)

        except requests.RequestException as e:
            self.logger.warning('url:%s, method:%s, kwargs:%s, error_msg:%s' % (url, method, str(kwargs), e))
            return None

def get_proxy():
    return choice(Response().get_proxy())


if __name__ == '__main__':
    a = Response()
    logging.basicConfig(filename='a', format='%(asctime)s %(name)s %(levelname)s: %(message)s',
                        level=logging.DEBUG)
    for i in range(100):
        print(get_proxy())
        print(a.get_response('get','http://www.httpbin.org/ip'))