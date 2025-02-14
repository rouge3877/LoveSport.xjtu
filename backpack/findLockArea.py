"""
我们至今还没有搞清楚这个findLockArea是干什么的，
但是我们可以通过这个接口获取到场地的信息

或许是用来查询场地是否被锁定，
但是我们还没有搞清楚这个锁定是什么意思
"""

import requests
import time
import json

# Disable SSL warnings (target is HTTP protocol using an IP address)
requests.packages.urllib3.disable_warnings()

# Request parameters
params = {
    "s_date": "2025-02-11",
    "serviceid": 42,
    "_": int(time.time() * 1000)  # Generate timestamp dynamically
}

# Request headers
headers = {
    "Host": "202.117.17.144",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "http://202.117.17.144/product/show.html?id=42",
    "X-Requested-With": "XMLHttpRequest",
}

# Send request
url = "http://202.117.17.144/product/findLockArea.html"
response = requests.get(url, params=params, headers=headers, verify=False)

# Handle response
if response.status_code == 200:
    data = response.json()
    # print("Available area list:")
    # for idx, area in enumerate(data.get("object", []), start=1):
    #     print(f"  {idx}. {area}")
    parsed_list = []
    for area in data.get("object", []):
        stock = area.get("stock", {})
        parsed_list.append({
            "sname": area.get("sname"),
            "s_date": stock.get("s_date"),
            "time_no": stock.get("time_no"),
            "status(Maybe Lock or not)": (area.get("status") == 1),
            "stockdetailids": area.get("id")
        })

    # 存在“场地10”出现在“场地2”之前的情况，因为“场地10”在字典序中排在“场地2”之前
    # 需要根据场地编号进行排序
    parsed_list.sort(key=lambda x: int(x["sname"][2:]))


    parsed_json = json.dumps(parsed_list, ensure_ascii=False, indent=4)
    print(json.dumps(parsed_list, ensure_ascii=False, indent=4))

    # Areas with is_available == True
    print("\n=========================================\n")
    print("Areas with is_available == True:")
    for idx, area in enumerate(parsed_list, start=1):
        if area["is_available"]:
            print(f"  {idx}. {area['sname']} {area['s_date']} {area['time_no']} {area['stockdetailids']}")
    print("\n=========================================\n")
    
else:
    print("Request failed. Status code:", response.status_code)
