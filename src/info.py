# 健康情况填报
import re
import dataclasses
import json

import requests

from utils import Url, Validater, Config


prompt = {
    "success": "提交成功",
    "refuse": "",
    "has_report": "只能0点至16点可以填报",
    "failed": ""
}
pattern = r"content.*?(?<=\')(.*?)(?=\')"

static_data = {
    "GetAreaUrl": "/SPCP/Web/Report/GetArea",
    "radioCount": "9",
    "checkboxCount": "0",
    "blackCount": "10"
}


@dataclasses.dataclass(repr=True, slots=True)
class _RatioData:
    ratio_x: str
    title_id: str
    selected_id: str
    option_name: str

    @classmethod
    def build_from_tuple(cls, tup: tuple[str, str, str, str]):
        if len(tup) != 4:
            raise ValueError("the argument must be a tuple containing 4 strings")
        return cls(*tup)


def _ext_resubmit_flag(text):
    return re.findall(pattern=r'<input name="ReSubmiteFlag" type="hidden" value="(.*?)" />',
                      string=text) or ""


def _build_pz_data():
    ...


@Validater(prompt_dict=prompt, pattern=pattern, proc_alias="students info report")
def main(session: "requests.Session", config: Config):
    text = session.get()
