import requests
import sys
import os

# 将 ../src（即 LoveSport/src）路径添加到 sys.path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from utilities import parse_lsp_config
from xjtuLogin import LoginHandler

def make_order(session: requests.Session) -> dict:
    """
    执行下单请求
    :param session: 已登录的session对象
    :return: 解析后的订单响应数据
    """
    # 创建订单请求URL
    order_url = "http://202.117.17.144/order/show.html?id=41"
    
    # 准备订单请求载荷（库存、地址等）
    payload = {
        "stock": {
            "336116": "1"
        },
        "istimes": "1",
        "address": "41",
        "stockdetailids": "3372030"
    }
    
    # 设置订单请求特有的 Headers
    headers = {
        "Origin": "http://202.117.17.144",
        "Referer": "http://202.117.17.144/order/show.html?id=41",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        # 发送 POST 请求
        response = session.post(
            order_url,
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        print(response.text)
        
        # 解析JSON响应
        json_data = response.json()
        
    except requests.JSONDecodeError:
        return {"success": False, "error": "响应格式异常"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    # 初始化登录处理器并进行登录
    handler = LoginHandler()
    
    # 执行登录流程
    config_path = "lsp.config"
    username, password = parse_lsp_config(config_path)
    login_success, login_result = handler.login(username, password)
    
    if not login_success:
        print(f"登录失败: {login_result}")
        return
    else:
        print("登录成功！")

    # 使用登录成功的session执行下单请求
    order_result = make_order(login_result)
    
    # 处理下单结果
    if order_result["success"]:
        print("order/show.html 成功！响应数据：")
        print(order_result["data"])
        # 这里可以添加业务逻辑处理，例如提取订单号等
    else:
        print(f"order/show.html 失败: {order_result.get('error', '未知错误')}")

if __name__ == "__main__":
    main()