import requests
import os
import json
import time
# 需要安装pycryptodome模块
from Crypto.Cipher import AES
import base64
import re
from urllib.parse import quote
import sys
import getopt

session = requests.session()
headers = {
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
}
headers_form = {
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded'
}
domain_name = 'http://stu.hfut.edu.cn/'
app_id = ''
app_name = ''
name = ''


def get_post_url():
    url = 'http://stu.hfut.edu.cn/xsfw/sys/emapfunauth/casValidate.do?service=/xsfw/sys/swmxsyqxxsjapp/*default/index.do'
    response = session.get(url=url, headers=headers)
    return response.url.split('?')[1]


def add_to_16(s):
    while len(s) % 16 != 0:
        s += (16 - len(s) % 16) * chr(16 - len(s) % 16)
    return str.encode(s)  # 返回bytes


def encrypt(text, key):
    aes = AES.new(str.encode(key), AES.MODE_ECB)
    encrypted_text = str(base64.encodebytes(aes.encrypt(add_to_16(text))),
                         encoding='utf8').replace('\n', '')
    return encrypted_text


def check_user_identy(username, password, key):
    password = encrypt(password, key)
    url = 'https://cas.hfut.edu.cn/cas/policy/checkUserIdenty?username=' + username + '&password=' + password + '&_=' + get_stamp(
    ).__str__()
    r = session.get(url=url, headers=headers)
    # print(r.headers)
    # print(r.request.headers)
    # print(r.text)
    return password


def get_stamp():
    return int(round(time.time() * 1000))


def jump_auth_with_key():
    """
    获取cookie
    :return:
    """
    jump_auth_url = 'http://stu.hfut.edu.cn/xsfw/sys/emapfunauth/casValidate.do?service=/xsfw/sys/swmxsyqxxsjapp/*default/index.do'
    session.get(url=jump_auth_url, headers=headers)
    JSESSIONID_url = 'https://cas.hfut.edu.cn/cas/vercode'
    session.get(url=JSESSIONID_url, headers=headers)

    LOGIN_FLAVORING_url = 'https://cas.hfut.edu.cn/cas/checkInitVercode?_=' + get_stamp().__str__()
    response = session.get(url=LOGIN_FLAVORING_url, headers=headers)
    return response.cookies.values()[0]


def login(username, password):
    url = 'https://cas.hfut.edu.cn/cas/login?' + get_post_url()
    data = {
        'username': username,
        'captcha': '',
        'execution': 'e2s1',  # 随意
        '_eventId': 'submit',
        'password': password,
        'geolocation': '',
        'submit': '登录'
    }
    headers = {
        'Content-Type':
        'application/x-www-form-urlencoded',
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    }

    response = session.post(url=url, data=data, headers=headers)
    try:
        global app_id
        global app_name
        global name
        html = response.text.replace('\n', '').replace('\r', '').replace(' ', '')
        real_name = re.findall(r'"roleId":"(.+)"}}', html)[0]
        r_list = re.search(r'PATH:path,(.+),RES_SERVER:', html).group(1).replace('"', '').split(',')
        app_id = r_list[0].replace('APPID:', '')
        app_name = r_list[1].replace('APPNAME:', '')
        name = real_name
#         print('[+]你好,{}...'.format(real_name))
        return True
    except Exception as e:
#         print(e.__str__())
        return False


def get_today_date():
    return time.strftime('%Y-%m-%d', time.localtime())


def pre_post():
    # 为了拿到cookie
    p_url1 = 'http://stu.hfut.edu.cn/xsfw/sys/swpubapp/MobileCommon/getSelRoleConfig.do'  # qw6a
    data = 'data=%7B%22APPID%22%3A%22{}%22%2C%22APPNAME%22%3A%22{}%22%7D'.format(app_id, app_name)
    session.post(url=p_url1, headers=headers_form, data=data)
    p_url2 = 'http://stu.hfut.edu.cn/xsfw/sys/swpubapp/MobileCommon/getMenuInfo.do'  # 5ngm
    session.post(url=p_url2, headers=headers_form, data=data)


def fill_form(SCT_SENDKEY=None):
    # 开始填写表单
    # pre_post() # 后面都使用5ngm
    # 下面开始填写表单

    def make_data():
        # 提交的数据
        url = 'http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/getStuXx.do'
        data = 'data=%7B%7D'
        response = session.post(url=url, headers=headers_form, data=data)
        r_json = json.loads(response.text)
        post_data = r_json['data']
        return post_data

    post_data = make_data()
#     print(post_data)

    post_data.update({"BY1": "1", "DZ_SFSB": "1"})
#     print(post_data)
    data = 'data={}'.format(quote(json.dumps(post_data, ensure_ascii=False).replace(' ', '')))
    post_url = 'http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/saveStuXx.do'

    response = session.post(url=post_url, headers=headers_form, data=data)
    print(response.text)
    print("FINISH")
    content = json.loads(response.text)['msg']
    if SCT_SENDKEY != None:
        session.get("https://sc.ftqq.com/" + SCT_SENDKEY + ".send?text=校园打卡+&desp=" + content) #server酱推送，可以填入自己的key


def submit(USERNAME, PASSWD, SCT_SENDKEY=None):
    key = jump_auth_with_key()
#     print(key)
    password = check_user_identy(USERNAME, PASSWD, key)
#     print(password)
    ok = login(USERNAME, password)
    if ok:
        pre_post()
        fill_form(SCT_SENDKEY)
        return

    else:
        print('登录失败哦....')


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "h", [])
        for opt, arg in opts:
            if opt == '-h':
                print('useage: \n    DailyCP.py <USERNAME> <PASSWD> \nor  \n    DailyCP.py <USERNAME> <PASSWD> <SCT_SENDKEY>')
                sys.exit(1)
        if len(args) != 2 and len(args) != 3:
            print('useage: \n    DailyCP.py <USERNAME> <PASSWD> \nor  \n    DailyCP.py <USERNAME> <PASSWD> <SCT_SENDKEY>')
            sys.exit(1)
    except getopt.GetoptError:
        print('useage: \n    DailyCP.py <USERNAME> <PASSWD> \nor  \n    DailyCP.py <USERNAME> <PASSWD> <SCT_SENDKEY>')
        sys.exit(1)
    else:
        USERNAME = str(args[0])
        PASSWD = str(args[1])
        SCT_SENDKEY = None
        if len(args) == 3:
            SCT_SENDKEY = str(args[2])
    print("Get Username And Passwd")
    print("Start")

    submit(USERNAME, PASSWD, SCT_SENDKEY)


if __name__ == '__main__':
    main(sys.argv[1:])
