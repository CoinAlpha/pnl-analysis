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
        str_to_sign = str(now_time) + "+" + headerMeta['path']
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
                raise Exception(-1,response_data.content)
            else:
                if data and 'code' in data:
                    if data.get('code') == 0:
                        if 'data' in data:
                            return data['data']
                        else:
                            return data
                    else:
                        raise Exception(response_data.status_code, response_data.text)
        else:
            raise Exception(response_data.status_code, response_data.text)

    def getHistOrders(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        headerMeta = {
            "path": "order/hist"
        }
        return self._request('GET', f"{self.group}/api/pro/v2/order/hist", params=params, headerMeta=headerMeta)

    def getBalance(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        headerMeta = {
            "path": "balance"
        }
        return self._request('GET', f"{self.group}/api/pro/v1/cash/balance", params=params, headerMeta=headerMeta)

    def listCurrentOrders(kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        headerMeta = {
            "path": "order/hist/current"
        }
        account_category = 'cash' if not params['account_category'] else params['account_category']
        return self._request('GET', f"{self.group}/api/pro/v1/{account_category}/order/hist/current", params=params, headerMeta=headerMeta)

    def getTicker(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        return self._request('GET', "api/pro/v1/ticker", params=params, auth=False)

    def listAsset(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        return self._request('GET', "api/pro/v2/assets", params=params, auth=False)

    def listAllProduct(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        return self._request('GET', "api/pro/v1/products", params=params, auth=False)
