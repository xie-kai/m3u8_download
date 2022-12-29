import os
import time
import asyncio
import aiohttp
import aiofiles
from ctools import cp
from m3utool.model import runtime
from m3utool.config import (USER_AGENT,
                    ASYNC_TIMEOUT,
                    ASYNC_REQUEST_LIMIT)
from m3utool.encryption import AESEncryption



class M3U8AsyncDownloader:

    async def download_manage(self, segments):
        self.target = None
        if not segments:
            cp.print_red("Segments Null Data, Exit Download! ")
            return
        timeout   = aiohttp.ClientTimeout(total=ASYNC_TIMEOUT)
        connector = aiohttp.TCPConnector(limit=ASYNC_REQUEST_LIMIT)
        headers = {"user-agent": USER_AGENT, "referer": self.m3u8_url}
        # 连接无效状态码 直接退出
        self.error_status_codes = (404, 410)
        # 生成AES解密器
        self.cipher = {}
        for index, item in self.keys.items():
            self.cipher[index] = AESEncryption(**item)
        # 生成segments文件夹
        segments_folder = os.path.join(
            self.file_path,
            self.file_name.replace(".mp4", ".SEGMENTS"))
        if not os.path.isdir(segments_folder):
            os.makedirs(segments_folder)
        self.target = segments_folder
        # 异步session
        async with aiohttp.ClientSession(
            headers=headers, connector=connector, timeout=timeout
        ) as session:
            tasks, self.serial = [], 1
            for index, segment in segments.items():
                filename = os.path.join(segments_folder, f"{index}.ts")
                task = self.__async_request(
                    session, segment["url"], filename, segment["encrypt"])
                tasks.append(task)
            startime = time.time()
            await asyncio.gather(*tasks)
            endtime  = time.time()
            cp.print_white(f"Successfully - RunTime: {runtime(endtime - startime)}")

    async def __async_request(self, session, url, filename, encrypt):
        while not os.path.isfile(filename):
            try:
                async with session.get(url) as response:
                    # 错误状态码
                    if response.status in self.error_status_codes:
                        raise ValueError("StatusCode Error:", response.status)
                    # 不成功便成仁
                    if response.status != 200:
                        # cp.print_red(f"请求状态码: {response.status}", end="")
                        await asyncio.sleep(1)
                        continue
                    # 解密和保存
                    await self.__sava_the_segment(
                        filename, await response.read(), encrypt)
                    break
            except (
                asyncio.TimeoutError,
                asyncio.exceptions.TimeoutError,
                aiohttp.client_exceptions.ClientOSError,
                aiohttp.client_exceptions.ClientPayloadError,
                aiohttp.client_exceptions.ServerDisconnectedError,
                aiohttp.client_exceptions.ClientConnectionError,
            ) as error:
                # cp.print_red(f"\r{error}", end="")
                await asyncio.sleep(1)
        # 下载进度条
        cp.progress_bar(self.serial, self.maximum)
        self.serial += 1

    async def __sava_the_segment(self, filename, content, encrypt):
        # 解密
        if not (encrypt is None):
            content = self.cipher[encrypt].decrypt(content)
        # 异步保存
        async with aiofiles.open(filename, "wb") as fp:
            await fp.write(content)
