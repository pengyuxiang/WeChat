# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function
from wspider import  chaojiying
import requests
import time
def yanzheng(url):
    headers={
        "Content-Type": "image/jpg"
    }
    now = time.time()
    html = requests.get('https://mp.weixin.qq.com/mp/verifycode?cert={}'.format(now), headers=headers)
    with open('test.jpg', 'wb') as a:
        a.write(html.content)
    #超级鹰
    chao = chaojiying.Chaojiying_Client('ddll2qqzz', 'passw0rd', '96001')
    inputcode = chao.PostPic(a.read(), 1902)
    print(inputcode)
    # inputcode = raw_input()

    data = {
        "cert": now,
        "input": inputcode,
        "appmsg_token": '',
    }
    headers2={
        "Accept": "* / *",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Content-Length": 47,

    }

    cookie = requests.post('https://mp.weixin.qq.com/mp/verifycode', data=data).cookies
    return cookie







