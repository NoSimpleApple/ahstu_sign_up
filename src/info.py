# 健康情况填报
import dataclasses
import json
from typing import Optional, Literal, NewType

import requests
from lxml import etree

from utils import Url, Validater, Config, ext_resubmit_flag

prompt = {
    "success": "提交成功",
    "refuse": "",
    "has_report": "只能0点至16点可以填报",
    "failed": ""
}
pattern = r"content.*?(?<=\')(.*?)(?=\')"
xpath_th_right_phone = "//div[contains(@class,'th_right phone')]//input[@id and @value]"
xpath_ratio_required = "//div[@class='th_right required validate radio_list']//input[@type='radio']"

mixin_fields = {
    "GetAreaUrl": "/SPCP/Web/Report/GetArea",
    "radioCount": "9",
    "checkboxCount": "0",
    "blackCount": "10",
    "Other": "无"
}

# 不作为可选配置
danger_radio_options = {
    # 是否疑似或就诊
    "radio_4": "否，身体健康无异常",
    # 是否有发热、咳嗽等症状
    "radio_5": "以上症状都没有",
    # 近14天是否到过中高风险地区（旅行、居住、中转换乘等）
    "radio_6": "否",
    # 近14天未到中高风险地区，但与来自中高风险地区回来人员有接触
    "radio_7": "否",
    # 近21天是否与已确诊病例接触
    "radio_8": "否",
}

TH_RIGHT_CLASS = NewType("TH_RIGHT_CLASS",
                         Literal["th_right phone",
                                 "th_right",
                                 "th_right required validate radio_list",
                                 "th_right  phone",
                                 "th_right  validate radio_list",
                                 "input-style validate "])

NODE_TYPE = NewType("NODE_TYPE", Literal["text", "radio"])


@dataclasses.dataclass(repr=True, init=True, kw_only=True)
class _BaseData:
    # @data-tid
    title_id: Optional[str]
    # value
    option_name: str
    # SelectedId in field PZData, uuid, @value
    selected_id: Optional[str]
    # @//input[contains(@name, "radio")]/@type
    node_type: NODE_TYPE
    # radio type rets 0, and text rets 2
    # option_type: Literal["0", "2"]

    def ret_pz_data(self):
        return NotImplemented


@dataclasses.dataclass(repr=True, init=True, kw_only=True)
class _RadioData(_BaseData):
    ratio_x: str
    option_type = "0"
    node_type = "radio"

    def ret_pz_data(self) -> dict:
        ...


@dataclasses.dataclass(repr=True, init=True, kw_only=True)
class _TextData(_BaseData):
    text_x: str
    option_type = "2"
    node_type = "text"


def _build_data_by_raw_conf(class_tag: TH_RIGHT_CLASS, *,
                            __raw_conf: dict[str, str], __html_tree) -> list[_RadioData | _TextData]:
    pair = []

    # option_name作为PZData域中的键OptionName
    for attr_name, option_name in __raw_conf.items():
        xpath_attr_type = f"//div[@class='{class_tag}']//input[" \
                          f"@name='{attr_name}'" \
                          f"]"

        attr_type_matched = __html_tree.xpath(xpath_attr_type + "/@type") or [""]

        # xpath不稳定，加大细粒度
        match attr_type := attr_type_matched.pop():
            case "radio":
                xpath_radio_x_common = f"//div[@class='{class_tag}']//input[" \
                                       f"@name='{attr_name}' and " \
                                       f"@data-optionname='{option_name}'" \
                                       f"]"
                attr_selected_uuid_matched = __html_tree.xpath(xpath_radio_x_common + "/@value") or [""]
                attr_data_tid_matched = __html_tree.xpath(xpath_radio_x_common +
                                                          "/parent::div[@class='item']/@data-tid") or [""]
                pair.append(_RadioData(title_id=attr_data_tid_matched.pop(),
                                       option_name=option_name,
                                       selected_id=attr_selected_uuid_matched.pop(),
                                       node_type=attr_type,
                                       ratio_x=attr_name))

            case "text":
                xpath_text_common = f"//div[@class='{class_tag}']//input[" \
                                    f"@name='{attr_name}'" \
                                    f"]"
                attr_data_tid_matched = __html_tree.xpath(xpath_text_common +
                                                          "/parent::div[@class='item']/@data-tid") or [""]
                pair.append(_TextData(title_id=attr_data_tid_matched.pop(),
                                      option_name=option_name,
                                      selected_id="",
                                      node_type=attr_type,
                                      text_x=attr_name))
            case _:
                continue

    return pair


def _build_pz_data():
    ...


def _merge_req_data(*args: dict[str, str | None]):
    ...


@Validater(prompt_dict=prompt, pattern=pattern, proc_alias="students info report")
def main(session: "requests.Session", config: "Config"):
    resp = session.get(url=Url.INFO_REPORT,
                       timeout=5)

    if text_type := resp.headers.get("Content-Type"):
        if not text_type.find("text/html"):
            pass

    tree = etree.HTML(resp.text)
    conf_sect_radio = config["Radio"]
    print(conf_sect_radio)
    _build_data_by_raw_conf()
