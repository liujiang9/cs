import json

import requests

url = "http://webapi.http.zhimacangku.com/getip?num=200&type=2&pro=&city=0&yys=0&port=11&pack=124527&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions="

try:
    r = requests.get(url)

    with open("proxies.txt", "w") as f:
        proxies = json.loads(r.text)

        for item in proxies["data"]:
            print(f"https://{item['ip']}:{item['port']}", file=f)
        else:
            print(r.status_code)
            print(r.text)

except requests.exceptions.RequestException as e:
    print(e)
