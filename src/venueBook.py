# Description: This file is used to book a venue in the library (STEP 1)
import requests
import json
import urllib
import time


from config import BasicInfo
from xjtuLogin import LoginHandler
from utilities import parse_lsp_config
from venueAvailability import VenueAvailability
from config import BookingConfig
from config import CaptchaConfig
from captchaSolver import CaptchaSolver


class ProductShow:
    def __init__(self, service_id, session):
        self.service_id = service_id
        self.headers = BookingConfig.product_show_headers
        self.url = BookingConfig.book_url['product_show']
        self.session = session
        self.param = {}

    def update_book_param(self, stock_s, stockdetailids):
        self.param = {
            "stock": stock_s, # {"336333": "1"}
            "istimes": "1",
            "address": str(self.service_id),
            "stockdetailids": stockdetailids
        }
        return self.param
    
    def update_book_header(self):
        # add "?id=address" to the referer's url
        # self.headers["Referer"] = self.headers["Referer"] + "?id=" + str(self.address)
        return self.headers
    
    def update_book_url(self):
        self.url = self.url + "?id=" + str(self.service_id)
        return self.url
    
    def book(self, stockdetailids):
        self.update_book_param(BasicInfo._3f_stock, stockdetailids)
        self.update_book_header()
        self.update_book_url()
        
        response = self.session.post(self.url, data=self.param, headers=self.headers)
        return response
    
class OrderShow:
    def __init__(self, service_id,session):
        self.service_id = service_id
        self.headers = BookingConfig.order_show_headers
        self.url = BookingConfig.book_url['order_show']
        self.session = session
        self.param = {}


    def update_book_param(self, stock_s, stockdetailids):
        self.param = {
            "stock": stock_s, # {"336333": "1"}
            "istimes": "1",
            "address": str(self.service_id),
            "stockdetailids": stockdetailids
        }
        return self.param
    
    def update_book_header(self):
        # add "?id=address" to the referer's url
        # self.headers["Referer"] = self.headers["Referer"] + "?id=" + str(self.address)
        return self.headers
    
    def update_book_url(self):
        self.url = self.url + "?id=" + str(self.service_id)
        return self.url
    
    def book(self, stockdetailids):
        self.update_book_param(BasicInfo._3f_stock, stockdetailids)
        self.update_book_header()
        self.update_book_url()
        
        response = self.session.post(self.url, data=self.param, headers=self.headers)
        return response
    
    def print_request(self):
        print("url: ", self.url)
        print("headers: ", self.headers)
        print("service_id: ", self.service_id)
        print("session: ", self.session)
        print("data: ", self.param)
        print("response: ", response)

    


if __name__ == "__main__":

    handler = LoginHandler()
    config_path = "lsp.config"
    student_id, password = parse_lsp_config(config_path)
    login_success, book_session = handler.login(student_id, password)
    if not login_success:
        print(f"登录失败: {book_session}")
        exit(1)
    else:
        print("登录成功！")


    # get the availability of the venue
    address = BasicInfo._3f_address
    stock = BasicInfo._3f_stock
    client = VenueAvailability(service_id=address)
    areas = client.get_availability(target_date="2025-02-13")

    # get the stockdetailids
    stockdetailids = "3373075"

    # book the venue
    booker = OrderShow(address, book_session)
    response = booker.book(stockdetailids)
    if response.status_code != 200:
        print(f"预约失败，状态码：{response.status_code}")
        exit(1)

    # captcha solver
    solver = CaptchaSolver(book_session)
    captcha_data, validation_data = solver.solve_captcha(book_session.get("http://202.117.17.144/gen"))

    check_url = f"{CaptchaConfig.BOOK_SERVER_URL}"
   
    stock_key = list(stock.keys())[0]
    stockdetail = {stock_key: stockdetailids}

    check_payload_param = {
        "activityPrice": 0,
        "activityStr": None,
        "address": str(address),
        "dates": None,
        "extend": None,
        "flag": "0",
        "isBulkBooking": None,
        "isbookall": "0",
        "isfreeman": "0",
        "istimes": "1",
        "mercacc": None,
        "merccode": None,
        "order": None,
        "orderfrom": None,
        "remark": None,
        "serviceid": None,
        "shoppingcart": "0",
        "sno": None,
        "stock": stock,
        "stockdetail": stockdetail,
        "stockdetailids": stockdetailids,
        "stockid": None,
        "subscriber": "0",
        "time_detailnames": None,
        "userBean": None,
        "venueReason": None
    }

    check_payload_yzm = validation_data
    check_payload_yzm["bgImageHeight"] = 0
    check_payload_yzm["sliderImageWidth"] = 0

    print("yzm: ", check_payload_yzm)

    payload = {
        "param": json.dumps(check_payload_param),
        "yzm": json.dumps(check_payload_yzm) + 'synjones' + captcha_data["id"] + 'synjones' + 'http://202.117.17.144:8071',
        "json": "true"
    }

    # post: two params, one is the param, the other is the yzm
    response = book_session.post(check_url, data=payload, headers=CaptchaConfig.HEADERS)
    if response.status_code == 200:
        result = response.json()
        print(f"验证结果: {result}")
    else:
        print(f"验证请求失败，状态码：{response.status_code}")
        exit(1)

    print("OrderShow response: ", response.json())

    orderid = None
    if response.json()["result"] == "2":
        print("预约成功！")
        orderid = response.json()["object"]["order"]["orderid"]
    else:
        print("预约失败！")
