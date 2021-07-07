from src.abstract.httpRequest.BaseRestApi import BaseRestApi
import hmac
import hashlib
import base64
import time


class AscendexRestApi(BaseRestApi):
    def __init__(self, key, secret, group, url):
        super().__init__(key, secret, url)
        self.group = group

    def _headers(self, headerMeta):
        now_time = int(time.time()) * 1000
        apiPath = 'info'
        str_to_sign = str(now_time) + "+" + headerMeta['path']
        print(str_to_sign)
        signature = base64.b64encode(
            hmac.new(self.secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
        return {
            "x-auth-signature": signature,
            "x-auth-timestamp": str(now_time),
            "x-auth-key": self.key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def check_response_data(response_data):
        if response_data.status_code == 200:
            try:
                data = response_data.json()
            except ValueError:
                raise Exception(response_data.content)
            else:
                if data and 'code' in data:
                    if data.get('code') == 0:
                        if data.get('data'):
                            return data['data']
                        else:
                            return data
                    else:
                        raise Exception(
                            "{}-{}".format(response_data.status_code, response_data.text))
        else:
            raise Exception(
                "{}-{}".format(response_data.status_code, response_data.text))
