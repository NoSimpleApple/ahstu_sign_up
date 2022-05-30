import random

import requests
import requests.auth

from utils import Url, Validater, Config

prompt = {
    "success": "",
    "refuse": "",
    "failed": "输入不能为空!",
    "has_report": ""
}
pattern = r"content.*?(?<=\')(.*?)(?=\')"


def _gene_vali_code():
    letters = "abcdefghijklmnopqrstABCDEFGHI0123456"
    return random.sample(letters, 4)


def _warp_req_data(username, password, vali_code, /, **kwargs):
    return dict(txtUid=username,
                txtPwd=password,
                codeInput=vali_code,
                StuLoginMode=str(1))


class SignUpAuth(requests.auth.AuthBase):

    def __init__(self):
        super(SignUpAuth, self).__init__()

    def __call__(self, req: requests.PreparedRequest):
        return req


@Validater(prompt_dict=prompt, pattern=pattern, proc_alias="logon")
def main(session: "requests.Session", config: Config):
    try:
        test_rsp = session.get(url=Url.LOGIN,
                               timeout=5)

        code = test_rsp.status_code

        if code >= 500:
            raise requests.HTTPError
        elif code >= 400:
            raise requests.ConnectionError

    except (requests.HTTPError,
            requests.Timeout):
        print(f"logon website is inaccessible")
        exit(1)

    except requests.TooManyRedirects:
        print("redirects too many, maybe your proxies performs faulty?")
        exit(2)

    except (requests.ConnectionError,
            requests.ConnectTimeout):
        print("check your local network configure")
        raise

    data_ = _warp_req_data(config.get("Common", "txtUid"),
                           config.get("Common", "txtPwd"),
                           str(_gene_vali_code()))

    resp = session.post(url=Url.LOGIN,
                        data=data_,
                        allow_redirects=False,
                        auth=SignUpAuth())

    return resp
