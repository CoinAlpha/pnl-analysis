#!/usr/bin/python
# -*- coding:utf-8 -*-

import json
import requests
from uuid import uuid1
from urllib.parse import urljoin


class BaseRestApi(object):

    def __init__(self, key, secret, url):
        self.url = url
        self.key = key
        self.secret = secret

    def _headers(self):
        raise NotImplementedError("header by exchange specifications")

    def _request(self, method, uri, timeout=5, auth=True, params=None):
        uri_path = uri
        data_json = ''
        if method in ['GET', 'DELETE']:
            if params:
                strl = []
                for key in sorted(params):
                    strl.append("{}={}".format(key, params[key]))
                data_json += '&'.join(strl)
                uri += '?' + data_json
                uri_path = uri
        else:
            if params:
                data_json = json.dumps(params)
                uri_path = uri + data_json

        headers = self._headers()
        url = urljoin(self.url, uri)
        if method in ['GET', 'DELETE']:
            response_data = requests.request(
                method, url, headers=headers, timeout=timeout)
        else:
            response_data = requests.request(method, url, headers=headers, data=data_json,
                                             timeout=timeout)
        return self.check_response_data(response_data)

    def check_response_data(response_data):
        raise NotImplementedError("response handler depends on the exchange")
