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


class Validater:
    def __init__(self, prompt_dict, pattern, proc_alias):
        self.prompt = prompt_dict
        self.pattern = pattern
        self.alias = proc_alias

    def __call__(self, func: Callable[..., "requests.Response"], ):

        def wrapper(*args, **kwargs) -> "requests.Response":
            prompt = self.prompt
            alias = self.alias
            resp = func(*args, **kwargs)

            try:
                text = getattr(resp, "text")
            except AttributeError as e:
                err_info = "wrapped function should return an instance of requests.Response"
                raise ValueError(err_info) from e

            match_results = re.findall(pattern=self.pattern,
                                       string=text) or ["return void"]

            # TODO: this part need to refactor
            if prompt["has_report"] in match_results:
                print(f"found that you had reported previously, return: {prompt['has_report']}")

            elif prompt["refuse"] in match_results:
                print(f"{alias} refused, return: {prompt['refuse']}")

            elif prompt["failed"] in match_results:
                print(f"failed and please retry later, return: {prompt['failed']}")

            elif prompt["success"] in match_results:
                print(f"{alias} runs successfully, return: {prompt['success']}")

            else:
                print(f"{alias} returns: {match_results.pop()}")
            ###

            return resp

        return wrapper


def ext_resubmit_flag(text):
    return (re.findall(pattern=r'<input name="ReSubmiteFlag" type="hidden" value="(.*?)" />',
                       string=text) or [""]).pop()
