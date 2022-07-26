from pathlib import Path
import sys

import requests
import requests.cookies

import _config
import login
import temperature
import info
import utils


def main(config):
    sess = requests.Session()
    sess.headers = utils.default_header()

    login.main(sess, config)

    sess.headers["Referer"] = utils.Url.CHOOSE_SYS
    temperature.main(sess)

    info.main(sess, config)
    sess.close()


if __name__ == '__main__':
    path = Path(__file__).parent.parent.joinpath("./conf")

    try:
        cfgs = _config.config(path)
    except FileNotFoundError:
        print(f"no valid configure file found in path {path}")

        # 使用pyinstaller打包时builtins.exit符号缺失，原因未知
        sys.exit(1)
    else:
        for cfg in _config.config(path):
            print(f"--------------User: {cfg['Common']['txtUid']}----------------")
            main(cfg)
