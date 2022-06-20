import dataclasses
import re
import sys
import configparser
from typing import Callable, TypeAlias

import requests

UA_WIN = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 " \
         "(KHTML, like Gecko) Chrome/99.0.7113.93 Safari/537.36"
UA_LINUX = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " \
           "(KHTML, like Gecko) Chrome/99.0.4855.102 Safari/537.36"

Config: TypeAlias = configparser.RawConfigParser
T_Response: TypeAlias = requests.Response


def default_header():
    header = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q =0.9,image/webp,image/apng,"
                  "*/*;q=0.8,application / signed - exchange; v = b3; q = 0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Pragma": "no-store",
        "User-Agent": UA_WIN,
        "Host": "xgb.ahstu.edu.cn",
        "Cache-Control": "no-store",
    }
    if sys.platform.startswith("linux"):
        header["User-Agent"] = UA_LINUX

    return header


@dataclasses.dataclass(slots=True)
class Url:
    LOGIN = "http://xgb.ahstu.edu.cn/spcp/web"
    CHOOSE_SYS = "http://xgb.ahstu.edu.cn/SPCP/Web/Account/ChooseSys"
    TEM_INFO = "http://xgb.ahstu.edu.cn/SPCP/Web/Temperature/StuTemperatureInfo"
    INFO_REPORT = "http://xgb.ahstu.edu.cn/SPCP/Web/Report/Index"
    PASSPORT = "http://xgb.ahstu.edu.cn/SPCP/Web/BackSchool/Index"


def validate(*, prompts, pattern, proc_alias):
    def decorator(func):

        def wrapper(*args, **kwargs):
            nonlocal prompts
            nonlocal proc_alias
            nonlocal pattern

            resp = func(*args, **kwargs)
            try:
                text = getattr(resp, "text")
            except AttributeError as e:
                err_info = "wrapped function should return an instance of requests.Response"
                raise ValueError(err_info) from e

            match_results = re.findall(pattern=pattern,
                                       string=text) or ["return void"]
            _match_prompt(match_results)

            return resp

        return wrapper

    def _match_prompt(seq_resp_text):
        nonlocal prompts
        nonlocal proc_alias

        # TODO: this part need to refactor
        if prompts["has_report"] in seq_resp_text:
            print(f"found that you had reported previously, return: {prompts['has_report']}")

        elif prompts["refuse"] in seq_resp_text:
            print(f"{proc_alias} refused, return: {prompts['refuse']}")

        elif prompts["failed"] in seq_resp_text:
            print(f"failed and please retry later, return: {prompts['failed']}")

        elif prompts["success"] in seq_resp_text:
            print(f"{proc_alias} runs successfully, return: {prompts['success']}")

        else:
            print(f"{proc_alias} returns: {seq_resp_text.pop()}")

    return decorator


def ext_resubmit_flag(text):
    return (re.findall(pattern=r'<input name="ReSubmiteFlag" type="hidden" value="(.*?)" />',
                       string=text) or [""]).pop()
