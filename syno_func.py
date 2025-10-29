import requests
import urllib3


def get_syno_sid(BASE_URL,USERNAME,PASSWORD):
    # BASE_URL = f"https://{DSM_HOST}:{DSM_PORT}"
    auth_url = f"{BASE_URL}/webapi/auth.cgi"
    params = {
        "api": "SYNO.API.Auth",
        "method": "login",
        "version": "7",
        "account": USERNAME,
        "passwd": PASSWORD,
        "session": "Chat",
        "format": "sid"
    }
    resp = requests.get(auth_url, params=params, verify=False)
    data = resp.json()
    if data.get("success"):
        print(f"登录成功, SID = {data['data']['sid']}")
        return data["data"]["sid"]
    else:
        raise Exception(f"登录失败: {data}")

def get_user_info(BASE_URL,SID):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = f"{BASE_URL}/webapi/entry.cgi"
    payload = {
        "api": "SYNO.Chat.User",
        "method": "list",
        "version": 3,
        "_sid": SID
    }

    resp = requests.post(url, data=payload, verify=False)
    data = resp.json()

    # 假设 data 是你从群晖 Chat API 获取到的用户数据
    if data.get("success"):
        users = data["data"]["users"]
        for u in users:
            # print(u)
            if u.get('type') != "":
                user_data = {
                    "user_id": u['user_id'],
                    "nickname": u.get('nickname', ''),
                    "username": u.get('username', ''),
                    "type": u.get('type', '')
                }

                # print(user_data)

        print("所有用户数据已增量更新完成")
    else:
        print("获取用户失败:", data)
