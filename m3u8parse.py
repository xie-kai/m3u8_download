import copy
import m3u8
from ctools import cp
from urllib.parse import urljoin
from m3utool.model import runtime
from m3utool.httpclient import M3U8HtppClient

class M3U8Parse:

    def _run_m3u8parae(self):
        self.playlists = dict()
        self.__parse_playlists()
        self.__parse_keys()
        return self.__parse_segments()

    def __get_request_parameter(self):
        if not self.__dict__.__contains__("request_parameter"):
            self.__dict__["request_parameter"] = dict()
        request_parameter = self.__dict__["request_parameter"]
        if not request_parameter.__contains__("headers"):
            request_parameter["headers"] = dict()
        request_parameter["headers"]["referer"] = self.m3u8_url

    def __parse_playlists(self):
        cp.print_yellow(f"\r{'Parsing The PlayLists': <26}", end="")

        if self.m3u8_obj.is_variant:
            self.playlists[self.m3u8_obj] = {
                "url": self.m3u8_url,
                "dumps": self.m3u8_obj.dumps()}

            # 获取播放列表中分辨率最高媒体数据
            playlist = sorted(
                self.m3u8_obj.playlists,
                key=lambda x: \
                    x.stream_info.resolution[0] \
                    + x.stream_info.resolution[1])[-1]

            self.__get_request_parameter()
            self.m3u8_url = urljoin(playlist.base_uri, playlist.uri)
            self.m3u8_obj = self.httpclient.load(
                self.m3u8_url, **self.request_parameter)
            cp.print_green(f"\r{'Parsing The PlayLists': <26}", end="")
            return self.__parse_playlists

    def __parse_keys(self):

        cp.print_yellow(f"\r{'Parsing The Keys': <26}", end="")
        self.keys = {i: key for i, key in enumerate(self.m3u8_obj.keys) if key}
        if self.keys:
            keys_tmp = {}
            for index, key in self.keys.items():
                uri = urljoin(key.base_uri, key.uri)
                # 请求密钥值
                self.__get_request_parameter()
                secret_key = self.httpclient.send_request(
                    uri, **self.request_parameter).content
                # 保存keys
                keys_tmp[index] = {"keys": key, "key": secret_key}
                if key.iv:
                    keys_tmp[index]["iv"] = key.iv
            self.keys = keys_tmp
            cp.print_green(f"\r{'Parsing The Keys': <26}", end="")

    def __parse_segments(self):
        cp.print_yellow(f"\r{'Parsing The Segments': <26}", end="")
        segments, self.playtime, self.maximum = {}, 0, 0
        # 判断m3u8是否存在有效数据
        if not self.m3u8_obj.is_endlist:
            cp.print_red(f"\rM3U8 Parsing Failure! \nM3U8 Url: {self.m3u8_url}")
            return segments

        for index, segm in enumerate(self.m3u8_obj.segments):
            encrypt = None
            url = urljoin(self.m3u8_obj.base_uri, segm.uri)
            for ikey, key in self.keys.items():
                if key["keys"] is segm.key:
                    encrypt = ikey
                    break
            segments[index] = {"url": url, "encrypt": encrypt}
            # 播放时长累加
            self.playtime += segm.duration

        self.playtime = runtime(self.playtime)
        self.maximum = len(segments)
        for index in copy.deepcopy(self.keys):
            self.keys[index].pop("keys")
        cp.print_green(f"\r{'M3U8 Parsing Success!': <26}")
        return segments
