from src.abstract.httpRequest.BaseRestApi import BaseRestApi
import hmac
import hashlib
import base64
import time


class AscendexRestApi(BaseRestApi):
    def __init__(self, key, secret, group, url):
        super().__init__(self, key, secret, url)
        self.group = group

    def _headers(self):
        now_time = int(time.time()) * 1000
        str_to_sign = str(now_time) + method + uri_path
        passphrase = base64.b64encode(
            hmac.new(self.secret.encode('utf-8'), self.passphrase.encode('utf-8'), hashlib.sha256).digest())
        return {
            "x-auth-signature": sign,
            "x-auth-timestamp": str(now_time),
            "x-auth-key": self.key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
