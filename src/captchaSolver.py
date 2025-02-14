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

        # print(f"生成人类轨迹：目标距离={target_distance}，总时间={total_time_ms}ms")

        # 初始化参数：添加自然抖动范围和过冲概率
        initial_shake = random.choices(
            [(-3, 3), (-5, 5), (-2, 2)], 
            weights=[0.6, 0.3, 0.1]
        )[0]
        overstep_prob = random.choices([0.3, 0.6, 0.9], weights=[0.7, 0.25, 0.05])[0]

        # 按下事件（模拟手指按压的自然抖动）
        track.append({
            "x": random.randint(*initial_shake),
            "y": random.gauss(0, 1.2),
            "type": "down",
            "t": current_time
        })
        current_time += random.randint(15, 40)

        # 动态阶段划分（基于行为分析数据）
        phase_config = [
            {'duration': 0.25, 'mode': 'accelerate', 'jitter': 0.3},    # 初始加速
            {'duration': 0.40, 'mode': 'variable',   'jitter': 0.5},    # 变速阶段
            {'duration': 0.20, 'mode': 'decelerate', 'jitter': 0.7},    # 减速接近
            {'duration': 0.15, 'mode': 'adjustment', 'jitter': 0.9}    # 最终调整
        ]

        # 智能过冲预测
        should_overstep = random.random() < overstep_prob
        final_distance = target_distance + random.randint(3,8) if should_overstep else target_distance
        final_distance = min(final_distance, max_x)

        # 生成主轨迹
        for phase in phase_config:
            phase_duration = int(total_time_ms * phase['duration'])
            phase_end_time = current_time + phase_duration
            phase_target = int(final_distance * (phase_config.index(phase)+1)/len(phase_config))
            phase_step = 0

            while current_time < phase_end_time and current_x < final_distance:
                # 动态速度控制
                if phase['mode'] == 'accelerate':
                    speed_factor = 1.8 - (current_x / final_distance)
                    step_size = random.randint(2,4) * speed_factor
                elif phase['mode'] == 'variable':
                    speed_factor = 0.8 + random.random()*0.4
                    step_size = random.choices([2,3,4], weights=[0.3,0.5,0.2])[0]
                elif phase['mode'] == 'decelerate':
                    remaining = final_distance - current_x
                    step_size = max(1, int(remaining * random.uniform(0.05, 0.2)))
                else:
                    step_size = random.choices([0,1,2], weights=[0.4,0.4,0.2])[0]

                # 时间生成算法
                time_base = random.choices([8,12,15], weights=[0.5,0.3,0.2])[0]
                time_var = int(time_base * (1 + (random.random()-0.5)*0.3))
                
                # 坐标更新
                current_x = min(final_distance, current_x + int(step_size))
                current_time += time_var

                # 生成Y轴自然抖动
                y_move = last_y * 0.3 + random.gauss(0, phase['jitter'])
                y_move = max(-4.5, min(4.5, y_move))
                last_y = y_move

                track.append({
                    "x": current_x,
                    "y": y_move,
                    "type": "move",
                    "t": current_time
                })

                # 随机暂停模拟（真实操作中的犹豫）
                if random.random() < 0.12:
                    pause_time = random.randint(2, 8) if phase['mode'] != 'adjustment' else random.randint(10,30)
                    current_time += pause_time

        # 智能过冲修正（模拟人类修正行为）
        if should_overstep and current_x > target_distance:
            overshoot = current_x - target_distance
            correction_pattern = random.choice(['stepback', 'vibration'])
            
            if correction_pattern == 'stepback':
                # 分步回退修正
                for _ in range(random.randint(1,3)):
                    step_back = random.randint(1, min(3, overshoot))
                    current_x -= step_back
                    overshoot -= step_back
                    current_time += random.randint(4, 8)
                    track.append({
                        "x": current_x,
                        "y": last_y + random.gauss(0, 0.3),
                        "type": "move",
                        "t": current_time
                    })
            else:
                # 振动修正模式
                for _ in range(random.randint(2,4)):
                    direction = 1 if random.random() < 0.5 else -1
                    vibrate_step = random.randint(1,2)
                    current_x = max(target_distance, min(final_distance, current_x + direction*vibrate_step))
                    current_time += random.randint(3, 6)
                    track.append({
                        "x": current_x,
                        "y": last_y + random.uniform(-0.5,0.5),
                        "type": "move",
                        "t": current_time
                    })

        # 最终精准定位（模拟微操作）
        while current_x != target_distance and len(track) < 150:
            step = 1 if current_x < target_distance else -1
            current_x += step
            current_time += random.choices([3,5,1], weights=[0.6,0.3,0.1])[0]
            track.append({
                "x": current_x,
                "y": last_y * 0.2 + random.gauss(0, 0.2),
                "type": "move",
                "t": current_time
            })

        # 抬起事件（带结束动作）
        track.append({
            "x": current_x + random.choices([-1,0,1], weights=[0.2,0.6,0.2])[0],
            "y": random.gauss(0, 2.5),
            "type": "up",
            "t": current_time + random.randint(20, 60)
        })

        # 后处理：确保时间轴和坐标合法性
        total_duration = track[-1]['t']
        if total_duration != total_time_ms:
            time_scale = total_time_ms / total_duration
            # print(f"时间轴缩放比例：{time_scale} = {total_time_ms} / {total_duration}")
            for point in track:
                point['t'] = int(point['t'] * time_scale)
        
        for point in track:
            point['x'] = max(0, min(point['x'], max_x))
            point['y'] = round(point['y'], 2)

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