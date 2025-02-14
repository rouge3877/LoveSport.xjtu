import json
import requests

def book_order(session: requests.Session):
    url = "http://202.117.17.144/order/book.html"
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/132.0.0.0 Safari/537.36"),
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "http://202.117.17.144",
        "Referer": "http://202.117.17.144/order/show.html?id=42"
    }
    
    # Construct the "param" form field payload (sample data)
    param_payload = {
        "activityPrice": 0,
        "activityStr": None,
        "address": "42",
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
        "remark": None
    }
    
    # Construct the "yzm" field payload using captcha-solver data.
    # Replace the trackList with your actual generated track points.
    yzm_payload = {
        "bgImageWidth": 260,
        "bgImageHeight": 0,
        "sliderImageWidth": 0,
        "sliderImageHeight": 159,
        "startSlidingTime": "2025-02-12T13:36:15.438Z",
        "entSlidingTime": "2025-02-12T13:36:17.782Z",
        "trackList": [
            {"x": 0, "y": 0, "type": "down", "t": 1109},
            # ... add additional track point dictionaries here ...
        ]
    }
    
    # Build form data with URL encoded JSON strings.
    form_data = {
        "param": json.dumps(param_payload),
        "yzm": json.dumps(yzm_payload),
        "json": "true"
    }
    
    response = session.post(url, headers=headers, data=form_data)
    return response

if __name__ == "__main__":
    # For testing purposes, use an authenticated session.
    # For example, you can login using LoginHandler from xjtuLogin.py.
    from xjtuLogin import LoginHandler
    config_path = "lsp.config"
    from utilities import parse_lsp_config

    handler = LoginHandler()
    student_id, password = parse_lsp_config(config_path)
    success, result = handler.login(student_id, password)
    
    if success:
        session = result
        resp = book_order(session)
        print("Response status:", resp.status_code)
        print("Response content:", resp.text)
    else:
        print("登录失败:", result)