"""
西安交通大学统一身份认证登录模块
使用AES-ECB模式加密传输密码，模拟浏览器完成OAuth2.0登录流程
"""
import requests
import time
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from typing import Tuple, Union

from utilities import parse_lsp_config
from utilities import encrypt_password
from config import LoginConfig


class LoginHandler:
    """登录流程处理器"""
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(LoginConfig.BASE_HEADERS)

    def _check_response(self, response: requests.Response, expected_code: int = 200) -> bool:
        """检查响应状态码"""
        if response.status_code != expected_code:
            raise ConnectionError(f"请求失败，状态码：{response.status_code}，URL：{response.url}")
        return True

    def _execute_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """封装统一请求方法"""
        try:
            resp = self.session.request(method, url, **kwargs)
            self._check_response(resp)
            return resp
        except requests.RequestException as e:
            raise ConnectionError(f"网络请求异常：{str(e)}")

    def _phase1_init_session(self):
        """阶段1：初始化会话获取基础Cookie"""
        self._execute_request('GET', LoginConfig.URLS['init'])

    def _phase2_oauth_authorize(self):
        """阶段2：处理OAuth2.0授权请求"""
        self._execute_request('GET', LoginConfig.URLS['oauth_authorize'],
                             params=LoginConfig.OAUTH_PARAMS)

    def _phase3_get_login_page(self):
        """阶段3：获取登录页面"""
        self._execute_request('GET', LoginConfig.URLS['login_page'])

    def _phase4_submit_credentials(self, username: str, encrypted_pwd: str) -> dict:
        """阶段4：提交登录凭证"""
        login_data = {
            "loginType": 1,            # 登录方式：账号密码登录
            "username": username,      # 统一身份认证账号
            "pwd": encrypted_pwd,      # AES加密后的密码
            "jcaptchaCode": ""         # 验证码(当前留空)
        }
        response = self._execute_request('POST', LoginConfig.URLS['submit_login'],
                                        json=login_data)
        json_data = response.json()
        if json_data.get('code') != 0:
            raise ValueError("登录失败: " + json_data.get('message', '未知错误'))
        return json_data['data']

    def _phase5_setup_session(self, token_key: str, member_id: str):
        """阶段5：设置会话参数"""
        # 设置用户身份
        self._execute_request('POST', LoginConfig.URLS['get_identity'],
                             data={'memberId': member_id})
        
        # 手动设置关键Cookie
        self.session.cookies.set('sid_code', f'workbench_login_jcaptcha_{self.session.cookies.get("JSESSIONID")}')
        self.session.cookies.set('memberID', member_id)
        self.session.cookies.set('open_Platform_User', token_key)

    def _phase6_final_redirect(self, username: str) -> str:
        """阶段6：获取最终重定向URL"""
        params = {
            'userType': 1,
            'personNo': username,            # 注意参数名差异
            '_': int(time.time() * 1000)     # 防缓存时间戳
        }
        response = self._execute_request('GET', LoginConfig.URLS['redirect_url'],
                                        params=params)
        json_data = response.json()
        if json_data.get('code') != 0:
            raise ValueError("获取重定向URL失败: " + json_data.get('message', '未知错误'))
        return json_data['data']

    def _phase7_validate_login(self) -> bool:
        """阶段7：验证最终登录状态"""
        try:
            # 访问需要登录的页面验证状态
            resp = self._execute_request('GET', 'http://202.117.17.144/index.html')
            return "用户未登录" not in resp.text
        except Exception:
            return False

    def login(self, username: str, password: str) -> Tuple[bool, Union[requests.Session, str]]:
        """
        执行完整登录流程
        :param username: 统一身份认证账号
        :param password: 密码
        :return: (是否成功, 成功返回Session/失败返回错误信息)
        """
        try:
            # 执行登录流程各阶段
            self._phase1_init_session()
            self._phase2_oauth_authorize()
            self._phase3_get_login_page()
            
            # 加密密码并提交登录
            encrypted_pwd = encrypt_password(password)
            login_data = self._phase4_submit_credentials(username, encrypted_pwd)
            
            # 提取并设置会话参数
            token_key = login_data['tokenKey']
            member_id = str(login_data['orgInfo']['memberId'])
            self._phase5_setup_session(token_key, member_id)
            
            # 处理重定向
            redirect_url = self._phase6_final_redirect(username)
            self._execute_request('GET', redirect_url, allow_redirects=True)
            
            # 最终验证
            if not self._phase7_validate_login():
                raise RuntimeError("登录状态验证失败")
            
            return True, self.session

        except Exception as e:
            return False, str(e)

# 使用示例 ------------------------------------------------------------------------
if __name__ == "__main__":
    # 测试登录（需替换实际账号密码）
    handler = LoginHandler()

    config_path = "lsp.config"
    student_id, password = parse_lsp_config(config_path)

    success, result = handler.login(student_id, password)
    
    if success:
        print("登录成功！")
        print("Cookies:", result.cookies.get_dict())
        # 示例：使用获取的Session访问其他接口
        # resp = result.get('需要登录的URL')
    else:
        print("登录失败:", result)