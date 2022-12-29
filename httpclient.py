import os
import m3u8
from ctools import cp
import requests, warnings
from requests.packages import urllib3
from m3utool.config import USER_AGENT, REQUEST_TIMEOUT


class M3U8HtppClient:

    def __init__(self, instance=None):
        self.instance = instance

    def load(self, url, **kwargs):
        response = self.send_request(url, **kwargs)
        return m3u8.loads(
            response.content.decode("utf-8"),
            m3u8._parsed_url(url))

    def loads(self, content, url=None):
        if os.path.isfile(content):
            with open(content, encoding="utf-8") as fileobj:
                content = fileobj.read()
        content = str(content).strip()
        if m3u8.is_url(url):
            url = m3u8._parsed_url(url)
        return m3u8.loads(content, url)

    def send_request(self, url, **kwargs):
        if not m3u8.is_url(url):
            raise requests.exceptions.URLRequired(cp.colored_red(url))
        self.request_parameter = kwargs
        self._initialization_request_parameter()
        while True:
            try:
                response = requests.request(url=url, **self.request_parameter)
                assert response.status_code == 200, f"\nRequest StatusCode: {cp.colored_red(response.status_code)}\nURL: {response.url}"
                if self.instance:
                    self.instance.__dict__["request_parameter"] = self.request_parameter
                print("\r", end="")
                return response
            except requests.exceptions.Timeout as error:
                print(error)
                cp.print_red("请求超时重试! ")

            except requests.exceptions.ConnectionError as error:
                print(error)
                cp.print_red("请检查网络连接是否正常! ")

    def _initialization_request_parameter(self):
        parameter = self.__dict__.get("request_parameter")
        # method
        method = parameter.get("method", "GET")
        parameter["method"] = str(method).strip().upper()
        # headers
        headers = {str(k).lower(): str(v) \
                      for k, v in parameter.get("headers", dict()).items()}
        headers["user-agent"] = headers.get("user-agent", USER_AGENT)
        parameter["headers"] = headers
        # timeout
        parameter["timeout"] = parameter.get("timeout", REQUEST_TIMEOUT)
        # verify
        if parameter.get("verify") is False:
            urllib3.disable_warnings()
            warnings.filterwarnings("ignore")
