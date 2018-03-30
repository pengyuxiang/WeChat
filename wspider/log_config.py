#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import logging.handlers

def createlog(filename,name):
    handler = logging.handlers.RotatingFileHandler(filename) #当日志文件大于maxBytes时，自动切分文件，最多有Bcakupcount个文件
    fmt = '%(name)s - %(levelname)s - %(asctime)s - %(pathname)s - %(message)s\n'

    formatter = logging.Formatter(fmt)  # 实例化formatter
    handler.setFormatter(formatter)  # 为handler添加formatter
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    hdr = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s: %(message)s')
    hdr.setFormatter(formatter)

    # 给logger添加上handler(用于打印)
    logger.addHandler(hdr)
    return logger

