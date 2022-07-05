import json
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests


class BaseRestApi(ABC):
    def __init__(self, key, secret, url):
        self.url = url
        self.key = key
        self.secret = secret

    @abstractmethod
    def _headers(self, header_meta=None):
        raise NotImplementedError("headers done by exchange specifications")

    def _request(self, method, uri, timeout=30, auth=True, params=None, header_meta=None):
        data_json = ""
        if method in ["GET", "DELETE"]:
            if params:
                strl = []
                for key in sorted(params):
                    strl.append("{}={}".format(key, params[key]))
                data_json += "&".join(strl)
                uri += "?" + data_json
        else:
            if params:
                data_json = json.dumps(params)
        if auth:
            headers = self._headers(header_meta)
        else:
            headers = {"Accept": "application/json"}

        url = urljoin(self.url, uri)
        if method in ["GET", "DELETE"]:
            response_data = requests.request(method, url, headers=headers, timeout=timeout)
        else:
            response_data = requests.request(method, url, headers=headers, data=data_json, timeout=timeout)
        return self.check_response_data(response_data)
