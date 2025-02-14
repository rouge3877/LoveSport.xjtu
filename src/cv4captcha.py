import cv2
import numpy as np

from config import CV4CaptchaConfig

class CaptchaMatcher:
    """
    滑块验证码匹配处理类, 提供 get_distance 接口用于外部调用：
        solver = CaptchaMatcher()
        distance = solver.get_distance(slider_image, background_image)
    """
    def __init__(self, config=CV4CaptchaConfig):
        """
        初始化Solver，可在此添加其它参数或全局变量
        """
        self.config = config

    def _get_alpha_channel_horizontally(self, img):
        """
        提取滑块上下边界（取alpha通道中非透明区域）
        """
        alpha_channel = img[:, :, 3]
        # 找到非透明区域的轮廓，只检测最外层轮廓
        contours, _ = cv2.findContours(alpha_channel, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # 获取最大轮廓（按面积排序）
        max_contour = max(contours, key=cv2.contourArea)
        # 计算轮廓边界框，返回上边界和下边界
        _, y, _, h = cv2.boundingRect(max_contour)
        upper = y
        lower = y + h
        return upper, lower

    def _crop_image_horizontally(self, img, upper, lower):
        """
        裁切图片，只保留上下边界之间部分
        """
        return img[upper:lower, :]

    def _preprocess_image(self, image, upper, lower, kernel_size):
        """
        对图像裁剪、模糊降噪及Canny边缘检测
        """
        # 1. 裁剪图片
        cropped = self._crop_image_horizontally(image, upper, lower)
        # 2. 高斯模糊降噪
        blurred = cv2.GaussianBlur(cropped, kernel_size, self.config.GAUSSIAN_BLUR_SIGMA_X)
        # 3. Canny边缘检测
        edges = cv2.Canny(blurred, self.config.CANNY_THRESHOLD1, self.config.CANNY_THRESHOLD2)
        return edges

    def _match_template(self, bg_edges, slider_edges, method=cv2.TM_CCOEFF_NORMED):
        """
        使用模板匹配，并返回滑块中心点及匹配度
        """
        slider_h, slider_w = slider_edges.shape[:2]
        res = cv2.matchTemplate(bg_edges, slider_edges, method)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        x, y = max_loc
        match = max_val
        slider_center = (x + slider_w // 2, y + slider_h // 2)
        return slider_center, match

    def _calcu_distance(self, bg_edges, slider_edges, show_match=False):
        """
        计算滑块距离起始点的偏移量
        """
        method_list = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
        center_list = []
        match_list = []
        for method in method_list:
            slider_center, match = self._match_template(bg_edges, slider_edges, method)
            center_list.append(slider_center)
            match_list.append(match)
        max_match = max(match_list)
        max_index = match_list.index(max_match)
        slider_center = center_list[max_index]

        if show_match:
            slider_h, slider_w = slider_edges.shape[:2]
            res = cv2.matchTemplate(bg_edges, slider_edges, method)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            x, y = max_loc
            print(f"匹配度：{max_val}")
            bg_edges_color = cv2.cvtColor(bg_edges, cv2.COLOR_GRAY2BGR)
            cv2.rectangle(bg_edges_color, (x, y), (x + slider_w, y + slider_h), (0, 255, 0), 2)
            cv2.circle(bg_edges_color, slider_center, 3, (0, 0, 255), -1)
            cv2.imshow('match', bg_edges_color)
            cv2.waitKey(0)

        # 计算滑块中心点与背景中心点的水平偏移量
        distance = slider_center[0] - slider_edges.shape[1] / 2
        return distance

    def get_distance(self, slider_cv_img, bg_cv_img, show_match=False):
        """
        外部调用接口，计算滑块与背景匹配得到的位移
        """
        upper, lower = self._get_alpha_channel_horizontally(slider_cv_img)
        slider_edges = self._preprocess_image(slider_cv_img, upper, lower, self.config.GAUSSIAN_BLUR_KERNEL_SIZE_SLIDER)
        bg_edges = self._preprocess_image(bg_cv_img, upper, lower, self.config.GAUSSIAN_BLUR_KERNEL_SIZE_BG)
        distance = self._calcu_distance(bg_edges, slider_edges, show_match)
        return distance

if __name__ == "__main__":
    # 测试代码
    solver = CaptchaMatcher()
    slider = cv2.imread("slider.png", cv2.IMREAD_UNCHANGED)
    bg = cv2.imread("bg.jpg")
    distance = solver.get_distance(slider, bg, show_match=True)
    print(f"滑块距离: {distance}")