import base64
import hashlib
import hmac
import time

from src.abstract.httpRequest.base_rest_api import BaseRestApi


class AscendexRestApi(BaseRestApi):
    def __init__(self, key, secret, group, url):
        super().__init__(key=key, secret=secret, url=url)
        self.group = group

    @staticmethod
    def check_response_data(response_data):
        if response_data.status_code == 200:
            try:
                data = response_data.json()
            except ValueError:
                raise Exception(-1, response_data.content)
            else:
                if data and "code" in data:
                    if data.get("code") == 0:
                        if "data" in data:
                            return data["data"]
                        else:
                            return data
                    else:
                        raise Exception(response_data.status_code, response_data.text)
        else:
            raise Exception(response_data.status_code, response_data.text)

    def get_hist_order(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        header_meta = {"path": "order/hist"}
        return self._request(
            "GET",
            f"{self.group}/api/pro/v2/order/hist",
            params=params,
            header_meta=header_meta,
        )

    def get_balance(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        header_meta = {"path": "balance"}
        return self._request(
            "GET",
            f"{self.group}/api/pro/v1/cash/balance",
            params=params,
            header_meta=header_meta,
        )

    def list_current_orders(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        header_meta = {"path": "order/hist/current"}
        account_category = "cash" if not params["account_category"] else params["account_category"]
        return self._request(
            "GET",
            f"{self.group}/api/pro/v1/{account_category}/order/hist/current",
            params=params,
            header_meta=header_meta,
        )

    def get_ticker(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        return self._request("GET", "api/pro/v1/ticker", params=params, auth=False)

    def list_asset(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        return self._request("GET", "api/pro/v2/assets", params=params, auth=False)

    def list_all_product(self, **kwargs):
        params = {}
        if kwargs:
            params.update(kwargs)
        return self._request("GET", "api/pro/v1/products", params=params, auth=False)

    def _headers(self, header_meta):
        now_time = int(time.time()) * 1000
        str_to_sign = str(now_time) + "+" + header_meta["path"]
        signature = base64.b64encode(
            hmac.new(
                key=self.secret.encode("utf-8"), msg=str_to_sign.encode("utf-8"), digestmod=hashlib.sha256
            ).digest()
        )
        return {
            "x-auth-signature": signature,
            "x-auth-timestamp": str(now_time),
            "x-auth-key": self.key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
