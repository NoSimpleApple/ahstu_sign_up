# 健康情况填报
import dataclasses
import enum
import json
from functools import reduce
from typing import Optional, Literal, NewType, TypeAlias, Mapping, Sequence

import requests
from lxml import etree

from utils import Url, Validater, Config, ext_resubmit_flag, default_header

prompt = {
    "success": "提交成功",
    "refuse": "只能0点至16点可以填报",
    "has_report": "",
    "failed": ""
}
pattern = r"content.*?(?<=\')(.*?)(?=\')"
xpath_th_right_phone = "//div[contains(@class,'th_right phone')]//input[@id and @value]"
xpath_ratio_required = "//div[@class='th_right required validate radio_list']//input[@type='radio']"

fields_mixin = {
    "GetAreaUrl": "/SPCP/Web/Report/GetArea",
    "radioCount": "9",
    "checkboxCount": "0",
    "blackCount": "10",
    "Other": "无"
}

# 不作为可选配置
fields_danger_radio_options = {
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


# 在此添加新的@class
class ThRightClass(enum.Enum):
    TH_RIGHT_PHONE = "th_right phone"
    TH_RIGHT = "th_right"
    TH_RIGHT_REQUIRED_VALIDATE_RADIO_LIST = "th_right required validate radio_list"
    TH_RIGHT__PHONE = "th_right  phone"
    TH_RIGHT_VALIDATE_RADIO_LIST = "th_right  validate radio_list"
    INPUT_STYLE_VALIDATE = "input-style validate"


T_th_right_class: TypeAlias = ThRightClass
T_node = NewType("T_node", Literal["text", "radio"])


@dataclasses.dataclass(repr=True, init=True, kw_only=True, slots=True)
class _BaseData:
    # @data-tid
    title_id: Optional[str]
    # value
    option_name: str
    # SelectedId in field PZData, uuid, @value
    selected_id: Optional[str]
    # @//input[contains(@name, "radio")]/@type
    node_type: T_node

    # radio type rets 0, and text rets 2
    # option_type: Literal["0", "2"]

    @property
    def fmt_pz_data(self):
        return NotImplemented

    @property
    def fmt_req_data(self):
        return NotImplemented


@dataclasses.dataclass(repr=True, init=True, kw_only=True, slots=True)
class _RadioData(_BaseData):
    ratio_x: str
    is_selected: bool
    option_type = "0"
    node_type = "radio"

    @property
    def fmt_pz_data(self):
        return NotImplemented

    @property
    def fmt_req_data(self) -> dict[str, str]:
        ratio_x = self.ratio_x

        if not ratio_x:
            raise ValueError("the field ratio_x got an unexpected void")
        return {ratio_x: self.selected_id if self.selected_id else ""}


@dataclasses.dataclass(repr=True, init=True, kw_only=True, slots=True)
class _TextData(_BaseData):
    text_x: str
    option_type = "2"
    node_type = "text"

    @property
    def fmt_pz_data(self):
        return NotImplemented

    @property
    def fmt_req_data(self) -> dict[str, str]:
        text_x = self.text_x

        if not text_x:
            raise ValueError("field ratio_x got an unexpected void")
        return {text_x: self.option_name}


def _build_data_by_raw_conf(class_tag: T_th_right_class | Sequence[ThRightClass], *,
                            __raw_conf: Mapping[str, str], __html_tree) -> list[_RadioData | _TextData]:
    pair = []

    if not isinstance(class_tag, Sequence):
        class_tag = (class_tag,)

    for tag in class_tag:
        # option_name作为PZData域中的键OptionName
        for attr_name, option_name in __raw_conf.items():
            xpath_attr_type = f"//div[@class='{tag}']//input[" \
                              f"@name='{attr_name}'" \
                              f"]"

            attr_type_matched = (__html_tree.xpath(xpath_attr_type + "/@type") or [""]).pop()

            # xpath不稳定，加大细粒度
            match attr_type_matched:
                case "radio":
                    xpath_radio_x_common = f"//div[@class='{tag}']//input[" \
                                           f"@name='{attr_name}' and " \
                                           f"@data-optionname" \
                                           f"]"
                    attr_selected_uuid_matched = (__html_tree.xpath(xpath_radio_x_common +
                                                                    "/@value") or [""]).pop()
                    attr_data_tid_matched = (__html_tree.xpath(xpath_radio_x_common +
                                                               "/parent::div[@class='item']/@data-tid") or [""]).pop()
                    attr_data_optionname_matched = (__html_tree.xpath(xpath_radio_x_common +
                                                                      "/@data-optionname") or [""]).pop()

                    pair.append(_RadioData(title_id=attr_data_tid_matched,
                                           option_name=attr_data_optionname_matched,
                                           selected_id=attr_selected_uuid_matched,
                                           node_type=attr_type_matched,
                                           ratio_x=attr_name,
                                           is_selected=attr_data_optionname_matched == option_name))

                case "text":
                    xpath_text_common = f"//div[@class='{tag}']//input[" \
                                        f"@name='{attr_name}'" \
                                        f"]"
                    attr_data_tid_matched = (__html_tree.xpath(xpath_text_common +
                                                               "/parent::div[@class='item']/@data-tid") or [""]).pop()
                    pair.append(_TextData(title_id=attr_data_tid_matched,
                                          option_name=option_name,
                                          selected_id="",
                                          node_type=attr_type_matched,
                                          text_x=attr_name))
                case _:
                    continue

    return pair


def _build_pz_data():
    ...


def _merge_req_data(*args: Mapping[str, str]) -> dict[str, str]:
    return dict(reduce(lambda f_kw, l_kw: f_kw | l_kw, args))


@Validater(prompt_dict=prompt, pattern=pattern, proc_alias="students info report")
def main(session: "requests.Session", config: "Config"):
    resp = session.get(url=Url.INFO_REPORT,
                       headers=default_header(),
                       timeout=5)

    if text_type := resp.headers.get("Content-Type"):
        if not text_type.find("text/html"):
            pass

    tree = etree.HTML(resp.text)
    resubmit_flag = ext_resubmit_flag(resp.text)
    normal_radio_data = _build_data_by_raw_conf(ThRightClass.TH_RIGHT_VALIDATE_RADIO_LIST,
                                                __raw_conf=config["Radio"],
                                                __html_tree=tree)
    danger_data = _build_data_by_raw_conf(ThRightClass.TH_RIGHT_VALIDATE_RADIO_LIST,
                                          __raw_conf=fields_danger_radio_options,
                                          __html_tree=tree)
    text_data = _build_data_by_raw_conf(ThRightClass.TH_RIGHT,
                                        __raw_conf=config["Text"],
                                        __html_tree=tree)
    # pz_data = None
    ex_data = {"StudentId": config["Common"]["txtUid"],
               "ReSubmiteFlag": resubmit_flag}

    req_data = _merge_req_data(dict(config["StuInfo"]), dict(config["Required"]),
                               *map(lambda _x_data: _x_data.fmt_req_data, normal_radio_data + text_data + danger_data),
                               ex_data, fields_mixin, fields_danger_radio_options)
    resp_post = requests.post(url=Url.INFO_REPORT,
                              headers=default_header(),
                              data=req_data)

    return resp_post
