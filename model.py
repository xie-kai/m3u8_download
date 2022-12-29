import os
import re
import shlex
import subprocess
from ctools import cp


def rename(file, suffix=""):
    # 后缀名解析
    if suffix:
        while isinstance(suffix, (list, tuple)):
            suffix = suffix[0]
        if not isinstance(suffix, str):
            suffix = ""
        else:
            if not suffix.startswith("."):
                suffix = "." + suffix
            suffix.strip()

    if file.endswith(suffix) and suffix:
        tmp = file.rsplit(suffix, 1)[0]
    else:
        tmp = file
        suffix = ""
    serial = 1
    # exists
    while os.path.exists(file):
        file = tmp + f".{serial}{suffix}"
        serial += 1
    return file.replace(" ", "_")


def runtime(rtime):
    rtime = round(rtime)
    hour, minute = divmod(rtime, 3600)
    minute, second = divmod(minute, 60)
    if not hour and not minute and not second:
        return 0
    hour = f"{hour}:" if hour else ""
    minute = f"{minute:0>2}:" if minute else "00:"
    second = f"{second:0>2}" if second else "00"
    return f"{hour}{minute}{second}"


def ffmpeg(target, video, delete=True):
    # 使用ffmpeg合并文件
    if not os.path.isdir(target):
        raise FileExistsError(cp.colored_red(f"{target} non-existent! "))
    print(f"start using the tool ffmpeg merge[delete: {delete}]...... ")
    pattern = re.compile(r".*?(\d+).*?")
    files = [f for f in next(os.walk(target))[-1] \
                if pattern.match(f)]
    files = sorted(files, \
                key=lambda x: int(pattern.match(x).group()))

    files = [os.path.join(target, f) for f in files]
    # FileList
    filelist = os.path.join(target, "FILELIST", "filelist.txt")
    folder = os.path.dirname(filelist)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with open(filelist, "w", encoding="utf-8") as fp:
        fp.writelines([f"file '{f}'\n" for f in files])

    # FFMPEG
    args = shlex.split(f"ffmpeg -f concat -safe 0 -i '{filelist}' -c copy '{video}' -y")
    try:
        subprocess.run(args, check=True, capture_output=True)
        if delete and os.path.isfile(video):
            os.remove(filelist)
            if not os.listdir(folder):
                os.rmdir(folder)
            for file in files:
                os.remove(file)
            if not os.listdir(target):
                os.rmdir(target)
            else:
                cp.print_red(f"Segments Don't Empty\nPath: {target}")
            return video
        else:
            cp.print_red(f"Don't Delete Segments\nPath: {target}")
            return None

    except FileNotFoundError:
        cp.print_red("ffmpeg uninstalled!")
        return None
