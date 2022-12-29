import os
import json
import time
import asyncio
from ctools import cp
from m3utool.config import FILE_PATH
from m3utool.m3u8parse import M3U8Parse
from m3utool.httpclient import M3U8HtppClient
from m3utool.model import rename, ffmpeg, runtime
from m3utool.async_request import M3U8AsyncDownloader


class M3U8Download(M3U8Parse, M3U8AsyncDownloader):

    def __init__(self, file_path=None):
        self.file_path = file_path
        self.httpclient = M3U8HtppClient(self)

    def _initialization(self):
        # file path
        if not self.file_path:
            self.file_path = FILE_PATH
            if not self.file_path:
                self.file_path = os.getcwd()
        # file name
        if not self.file_name:
            self.file_name = "index.mp4"
        else:
            self.file_name = str(self.file_name).strip()
            if len(self.file_name.rsplit(".", 1)) == 1:
                self.file_name += ".mp4"
        # video
        self.video = rename(os.path.join(self.file_path, self.file_name), "mp4")
        self.file_name = os.path.basename(self.video)

    def load(self, url, file_name=None, file_path=None, open_download=True, delete=True, **kwargs):
        self.m3u8_obj = self.httpclient.load(url, **kwargs)
        self.m3u8_url = url
        self.file_name = file_name
        self.file_path = file_path if file_path else self.file_path
        self.__run_m3u8(open_download, delete)

    def loads(self, content, url=None, file_name=None, file_path=None, open_download=True, delete=True):
        self.m3u8_obj = self.httpclient.loads(content, url)
        self.m3u8_url = url
        self.file_name = file_name
        self.file_path = file_path if file_path else self.file_path
        self.__run_m3u8(open_download, delete)

    def __run_m3u8(self, open_download, delete):
        self._initialization()
        self.delete = bool(delete)
        segments = self._run_m3u8parae()
        # 显示解析信息 不下载
        cp.print_magenta(f"FileName: {self.file_name}")
        cp.print_magenta(f"Storage: {self.file_path}")
        cp.print_magenta(f"Encryption: {bool(self.keys)}")
        cp.print_magenta(f"PlayTime: {self.playtime}")
        # 保存
        folder = os.path.join(self.file_path, "test")
        if not os.path.isdir(folder):
            os.makedirs(folder)
        file = os.path.join(
            folder, self.file_name.replace(".mp4", ".m3u8"))
        with open(file,"w", encoding="utf-8") as fp:
            json.dump(
                obj={
                   "url": self.m3u8_url,
                   "file_name": self.file_name,
                   "content": self.m3u8_obj.dumps()},
                fp=fp,
                ensure_ascii=False,
                indent=4)
        # 不下载文件 只做展示
        if not open_download:
            print(f"M3U8_Url: {self.m3u8_url}")
            print(f"Video: {self.video}")
            print(f"Maximum: {self.maximum}")
            print("Keys:")
            for i, key in self.keys.items():
                cp.print_yellow(f"{i}: {key}")
            print("Playlist: ")
            for play in self.playlists.values():
                cp.print_yellow(f"Url: {play['url']}")
                cp.print_yellow(f"Dumps:\n{play['dumps']}")
            cp.print_magenta(f"File: {file}\n")
        else:
            start = time.time()
            try:
                # 开始下载
                asyncio.run(self.download_manage(segments))
                # 使用ffmpeg合并文件
                if segments:
                    completion = lambda x: len(next(os.walk(x))[-1]) >= self.maximum
                    if completion(self.target) and delete:
                        self.delete = True
                    ffmpeg(self.target, self.video, self.delete)
            except KeyboardInterrupt:
                cp.print_red("download aborted")
            end = time.time()
            cp.print_yellow(f"download runtime: {runtime(end - start)}")
            if os.path.isfile(self.video):
                cp.print_yellow(f"Video: {self.video}")