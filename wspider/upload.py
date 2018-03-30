# -*- coding: utf-8 -*-
# coding=utf-8
import oss2
import logging
import os

import uuid

# 阿里云oss 相关参数.
OSS_ACCESS_KEY = 'LTAIkAyF3705B6J7'
OSS_ACCESS_KEY_SECRET = 'itevqE2BRRStNgLe1FAb3d3qMHgrUV'
OSS_BUCKET_NAME = 'abc-crawler'
OSS_ENDPOINT = 'http://oss-cn-hangzhou.aliyuncs.com'




class Uploader(object):

    def __init__(self):
        self.bucket = oss2.Bucket(oss2.Auth(OSS_ACCESS_KEY, OSS_ACCESS_KEY_SECRET), OSS_ENDPOINT,OSS_BUCKET_NAME)
        self.logger = logging.getLogger("Uploader")

    def upload_file(self,oss_path,save_path):
        try:
            result = self.bucket.put_object_from_file(oss_path,save_path)
            self.logger.info('upload oss result: %s, status : %s', result, result.status)
            if result.status != 200:
                self.logger.error('upload file %s failed with result %s', save_path ,result.status)
                return False
            else:
                self.logger.info('upload file %s ok, now remove temp file',save_path)
                return True
        except Exception, e:
            self.logger.error('upload file %s failed, error %s', save_path, e.message)
            return False



uploader = Uploader()