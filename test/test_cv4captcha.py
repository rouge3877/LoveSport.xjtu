import sys
import os

# 将 ../src（即 LoveSport/src）路径添加到 sys.path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import cv2
from cv4captcha import CaptchaMatcher


def test_cv4captcha(slider_path, bg_path):
    # 读取slider图像（包含Alpha通道）
    slider = cv2.imread(slider_path, cv2.IMREAD_UNCHANGED)
    if slider is None:
        raise FileNotFoundError(f"滑块图像 {slider_path} 不存在")
    
    # 读取background图像
    bg = cv2.imread(bg_path)
    if bg is None:
        raise FileNotFoundError(f"背景图像 {bg_path} 不存在")
    
    solver = CaptchaMatcher()
    distance = solver.get_distance(slider, bg, show_match=True)
    print(f"滑块距离: {distance}")

if __name__ == "__main__":

    flase_path = "./.false_captcha"
    for i in range(100):
        slider_path = os.path.join(flase_path, f"slider_{i}.png")
        bg_path = os.path.join(flase_path, f"bg_{i}.jpg")
        if os.path.exists(slider_path) and os.path.exists(bg_path):
            print(f"测试：{slider_path} 和 {bg_path}")
            test_cv4captcha(slider_path, bg_path)
        else:
            continue
