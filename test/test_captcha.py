import os
import time
import cv2
import sys
import requests

# 将 ../src（即 LoveSport/src）路径添加到 sys.path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config import CaptchaConfig
from captchaSolver import CaptchaSolver


def test_captcha(req, test_times: int = 100, test_gap: float = 1.1):
    pass_count = 0
    false_path = "./.false_captcha"
    if os.path.exists(false_path):
        for file in os.listdir(false_path):
            os.remove(os.path.join(false_path, file))
    else:
        os.mkdir(false_path)

    for i in range(test_times):
        print(f"第 {i+1} 次测试")
        gen_url = f"{CaptchaConfig.TEST_SERVER_URL}/gen"
        response = req.session.get(gen_url, headers=CaptchaConfig.HEADERS)

        captcha_data, validation_data = req.solve_captcha(response)

        check_url = f"{CaptchaConfig.TEST_SERVER_URL}/check"
        resp = req.session.post(
            check_url,
            params={"id": captcha_data["id"]},
            json=validation_data,
            headers=CaptchaConfig.HEADERS
        )
        if resp.status_code == 200:
            result = resp.json()
            try_result = result
        else:
            print(f"验证请求失败，状态码：{resp.status_code}")
            try_result = False
            exit(1)
            

        print(f"Captcha ID: {captcha_data['id']}")
        print(f"验证结果: {try_result}")
        if try_result:
            pass_count += 1
        else:
            slider, bg, _ = req._parse_captcha_data(captcha_data)
            cv2.imwrite(os.path.join(false_path, f"slider_{i}.png"), slider)
            cv2.imwrite(os.path.join(false_path, f"bg_{i}.jpg"), bg)
        time.sleep(test_gap)
    print(f"测试完成，通过率: {pass_count}/{test_times}")

if __name__ == "__main__":
    session = requests.Session()
    solver = CaptchaSolver(session)
    # 可执行测试
    test_captcha(solver, test_times=100, test_gap=1.1)