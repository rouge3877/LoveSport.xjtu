import time
import json
import random
import base64
import io
import os
import cv2
import numpy as np
from PIL import Image
from typing import Tuple
import requests

from cv4captcha import CaptchaMatcher
from config import CaptchaConfig

class CaptchaSolver:
    def __init__(self, session: requests.Session):
        self.session = session
        # ...existing initialization if needed...

    def _url2img(self, url: str) -> np.ndarray:
        image = Image.open(io.BytesIO(base64.b64decode(url.split(",")[-1])))
        image_np = np.array(image)
        if image.mode == "RGB":
            return cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        elif image.mode == "RGBA":
            return cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGRA)
        return image_np

    def _parse_captcha_data(self, captcha_data: dict):
        id = captcha_data["id"]
        bg_url = captcha_data["captcha"]["backgroundImage"]
        slider_url = captcha_data["captcha"]["sliderImage"]
        # print(f"获取验证码成功 ID: {id}")
        bg = self._url2img(bg_url)
        slider = self._url2img(slider_url)
        return slider, bg, id
    
    def _human_track_generate(self, target_distance: int, total_time_ms: int = 2150) -> list:
        track = []
        current_time = 0
        current_x = 0
        last_y = 0
        max_x = CaptchaConfig.WEB_BG_IMAGE_WIDTH

        # 初始化参数优化
        initial_shake = random.choices(
            [(-2, 2), (-3, 3), (-1, 1)], 
            weights=[0.7, 0.2, 0.1]
        )[0]
        overstep_prob = random.choices([0.25, 0.45], weights=[0.8, 0.2])[0]

        # 按下事件（更紧凑的时间）
        track.append({
            "x": random.randint(*initial_shake),
            "y": round(random.gauss(0, 0.8), 1),
            "type": "down",
            "t": current_time
        })
        current_time += random.randint(8, 15)

        # 阶段配置优化（更密集的时间分布）
        phase_config = [
            {'duration': 0.18, 'mode': 'accelerate', 'jitter': 0.25},  # 加速阶段
            {'duration': 0.55, 'mode': 'variable',   'jitter': 0.4},   # 主移动阶段
            {'duration': 0.15, 'mode': 'decelerate', 'jitter': 0.6},   # 减速阶段
            {'duration': 0.12, 'mode': 'adjustment', 'jitter': 0.8}    # 最终调整
        ]

        # 智能过冲控制
        final_distance = target_distance
        if random.random() < overstep_prob:
            final_distance += random.randint(2, 5)
            final_distance = min(final_distance, max_x)

        # 生成主轨迹（时间参数优化）
        for phase in phase_config:
            phase_duration = int(total_time_ms * phase['duration'])
            phase_end_time = current_time + phase_duration
            base_speed = random.uniform(0.8, 1.2)  # 速度波动系数

            while current_time < phase_end_time and current_x < final_distance:
                # 动态步长控制
                if phase['mode'] == 'accelerate':
                    progress = current_x / final_distance
                    step_size = random.choices([2,3,4], weights=[0.2, 0.5, 0.3])[0]
                    step_size = int(step_size * (1.5 - progress))
                elif phase['mode'] == 'variable':
                    step_size = random.choices([1,2,3], weights=[0.3, 0.5, 0.2])[0]
                elif phase['mode'] == 'decelerate':
                    remaining = final_distance - current_x
                    step_size = max(1, int(remaining * random.uniform(0.1, 0.3)))
                else:
                    step_size = random.choices([0,1], weights=[0.4, 0.6])[0]

                # 紧凑时间生成（核心修改点）
                time_var = random.choices([4,6,8], weights=[0.5,0.3,0.2])[0]
                time_var = int(time_var * base_speed * (0.9 + random.random()*0.2))
                
                current_x = min(final_distance, current_x + step_size)
                current_time += time_var

                # Y轴抖动生成
                y_move = last_y * 0.2 + random.gauss(0, phase['jitter'])
                y_move = round(max(-3.5, min(3.5, y_move)), 1)

                track.append({
                    "x": current_x,
                    "y": y_move,
                    "type": "move",
                    "t": current_time
                })

                # 微型停顿（保持自然性）
                if random.random() < 0.15:
                    current_time += random.choices([1,2,3], weights=[0.6,0.3,0.1])[0]

        # 过冲修正优化
        if current_x > target_distance:
            overshoot = current_x - target_distance
            correction_steps = min(3, overshoot)
            
            for _ in range(correction_steps):
                current_x -= 1
                current_time += random.choices([2,3,4], weights=[0.6,0.3,0.1])[0]
                track.append({
                    "x": current_x,
                    "y": round(last_y + random.uniform(-0.3,0.3), 1),
                    "type": "move",
                    "t": current_time
                })

        # 最终微调（时间间隔压缩）
        precision_steps = random.randint(1, 2)
        for _ in range(precision_steps):
            if current_x == target_distance:
                break
            step = 1 if current_x < target_distance else -1
            current_x += step
            current_time += random.choices([2,3], weights=[0.7,0.3])[0]
            track.append({
                "x": current_x,
                "y": round(last_y * 0.1 + random.gauss(0, 0.1), 1),
                "type": "move",
                "t": current_time
            })

        # 抬起事件（紧凑时间）
        track.append({
            "x": current_x,
            "y": round(random.gauss(0, 1.5), 1),
            "type": "up",
            "t": current_time + random.randint(8, 15)
        })

        # 时间轴校准优化
        total_duration = track[-1]['t']
        if abs(total_duration - total_time_ms) > 50:
            ratio = total_time_ms / total_duration
            for p in track:
                p['t'] = int(p['t'] * ratio)
        
        # 最终坐标修正
        for p in track:
            p['x'] = min(max_x, max(0, p['x']))
            if p['type'] == 'up':
                p['x'] = min(max_x, target_distance + random.choice([-1,0,1]))

        return track

    def solve_captcha(self, response: requests.Response) -> Tuple[bool, dict]:
        if response.status_code != 200:
            raise Exception(f"获取验证码失败，状态码：{response.status_code}")
        captcha_data = response.json()
        slider, bg, captcha_id = self._parse_captcha_data(captcha_data)
        solver = CaptchaMatcher()
        distance = solver.get_distance(slider, bg)
        scale = CaptchaConfig.WEB_BG_IMAGE_WIDTH / bg.shape[1]
        distance = int(distance * scale)
        random.seed(time.time())
        track_time = random.randint(2200, 2300)
        track_list = self._human_track_generate(distance, track_time)
        delta = track_list[-1]["t"]
        start_time = time.strftime("%Y-%m-%dT%H:%M:%S.601Z", time.gmtime())
        end_time = time.strftime("%Y-%m-%dT%H:%M:%S.720Z", time.gmtime(time.time() + delta / 1000))
        validation_data = {
            "bgImageWidth": CaptchaConfig.WEB_BG_IMAGE_WIDTH,
            "bgImageHeight": CaptchaConfig.WEB_BG_IMAGE_HEIGHT,
            "sliderImageWidth": CaptchaConfig.WEB_SLIDER_IMAGE_WIDTH,
            "sliderImageHeight": CaptchaConfig.WEB_SLIDER_IMAGE_HEIGHT,
            "startSlidingTime": start_time,
            "entSlidingTime": end_time,
            "trackList": track_list
        }

        return captcha_data, validation_data
        # check_url = f"{CaptchaConfig.SERVER_URL}/check"
        # resp = self.session.post(
        #     check_url,
        #     params={"id": captcha_id},
        #     json=validation_data,
        #     headers=CaptchaConfig.HEADERS
        # )
        # if resp.status_code == 200:
        #     result = resp.json()
        #     print(f"验证结果: {result}")
        #     return True, captcha_data, validation_data
        # print(f"验证请求失败，状态码：{resp.status_code}")
        # return False, captcha_data, validation_data

if __name__ == "__main__":
    pass