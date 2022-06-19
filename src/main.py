import requests
import requests.cookies

import login
import temperature
import info
import utils


def main():
    sess = requests.Session()
    sess.headers = utils.default_header()

    login_resp = login.main(sess)

    sess.headers["Referer"] = utils.Url.CHOOSE_SYS
    tem_resp = temperature.main(sess)

    # info_resp = info.main(sess)


if __name__ == '__main__':
    main()
