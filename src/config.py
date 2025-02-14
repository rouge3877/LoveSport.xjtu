import os
import sys
from dataclasses import dataclass
from Crypto.Cipher import AES

@dataclass
class BasicInfo:
    _1f_stock = {"336468": "1"}
    _1f_address = 41

    _3f_stock = {"336333": "1"}
    _3f_address = 42


class VenueAvailabilityConfig:
    """场馆可用性查询相关配置参数"""
    # 请求头配置
    BASE_HEADERS = {
        'Host': '202.117.17.144',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }

    # Referer地址模板
    REFERER_TEMPLATE = "http://202.117.17.144/product/show.html?id={service_id}"

    # 接口URL集合
    URLS = {
        'findokarea': 'http://202.117.17.144/product/findOkArea.html',
        'findlockarea': 'http://202.117.17.144/product/findLockArea.html'
    }

    # 默认请求参数
    DEFAULT_PARAMS = {
        'request_timeout': 10,    # 默认请求超时时间（秒）
        'cache_ttl': 60           # 默认缓存有效期（秒）
    }

@dataclass
class VenueAreaStruct:
    """场馆区域数据结构化表示"""
    name: str          # 场地名称（如"场地1"）
    date: str          # 日期（格式"YYYY-MM-DD"）
    time_slot: str     # 时间段编号
    is_available: bool # 当前是否可用
    detail_id: str     # 库存详情ID

class LoginConfig:
    """登录流程相关配置参数"""
    # AES加密参数（与前端保持一致）
    AES_KEY = b'0725@pwdorgopenp'  # 硬编码在网页中的AES密钥
    AES_MODE = AES.MODE_ECB        # 加密模式
    BLOCK_SIZE = AES.block_size    # AES块大小(16字节)

    # 请求头配置
    BASE_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Referer': 'http://card.xjtu.edu.cn/'  # 伪装来源页面
    }

    # 接口URL集合
    URLS = {
        'init': 'http://202.117.17.144/xjtu/cas/login.html',       # 初始化接口
        'oauth_authorize': 'http://org.xjtu.edu.cn/openplatform/oauth/authorize',  # OAuth认证
        'login_page': 'http://org.xjtu.edu.cn/openplatform/login.html',            # 登录页面
        'submit_login': 'http://org.xjtu.edu.cn/openplatform/g/admin/login',       # 提交登录
        'get_identity': 'http://org.xjtu.edu.cn/openplatform/g/admin/getUserIdentity',  # 获取身份
        'redirect_url': 'http://org.xjtu.edu.cn/openplatform/oauth/auth/getRedirectUrl' # 重定向URL
    }

    # OAuth2.0参数
    OAUTH_PARAMS = {
        'appId': '1439',                     # 应用ID(固定值)
        'redirectUri': 'http://202.117.17.144/xjtu/cas/oauth2url.html',  # 回调地址
        'responseType': 'code',              # 响应类型
        'scope': 'user_info',                # 权限范围
        'state': '1'                         # 状态参数
    }

class CaptchaConfig:
    BOOK_SERVER_URL = "http://202.117.17.144/order/book.html"
    TEST_SERVER_URL = "http://202.117.17.144:8071"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.124 Safari/537.36"
    }
    WEB_BG_IMAGE_WIDTH = 260
    WEB_BG_IMAGE_HEIGHT = 159
    WEB_SLIDER_IMAGE_WIDTH = 49
    WEB_SLIDER_IMAGE_HEIGHT = 159

@dataclass
class CV4CaptchaConfig:
    """
    滑块验证码处理相关的配置参数
    """
    # 高斯模糊核大小：用于降噪（背景图和滑块图分别设置）
    GAUSSIAN_BLUR_KERNEL_SIZE_BG = (3, 3)
    GAUSSIAN_BLUR_KERNEL_SIZE_SLIDER = (9, 9)
    # 高斯模糊X方向标准差：0表示自动计算模糊程度
    GAUSSIAN_BLUR_SIGMA_X = 0
    # Canny边缘检测阈值
    CANNY_THRESHOLD1 = 200
    CANNY_THRESHOLD2 = 450
    # 轮廓匹配阈值（此处暂未使用，可用于后续判断匹配度）
    MATCH_THRESHOLD = 0.3
    # 裁剪扩展像素（滑块高度额外保留的边缘区域）
    CROP_PADDING = 10

class BookingConfig:
    """预约流程相关配置参数"""        
    book_url = {"product_show": "http://202.117.17.144/product/show.html",
                "order_show":   "http://202.117.17.144/order/show.html"}


    product_show_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "202.117.17.144",
        "Origin": "http://202.117.17.144",
        "Pragma": "no-cache",
        "Proxy-Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    order_show_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "202.117.17.144",
        "Origin": "http://202.117.17.144",
        "Pragma": "no-cache",
        "Proxy-Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }



