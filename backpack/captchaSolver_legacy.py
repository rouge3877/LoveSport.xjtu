import requests
import json
import time
import random
import cv2
import numpy as np
from PIL import Image
import io
import base64
from cv4captcha import CaptchaMatcher



# 配置参数
SERVER_URL = "http://202.117.17.144:8071"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 网页验证码背景实际尺寸
WEB_BG_IMAGE_WIDTH = 260
WEB_BG_IMAGE_HEIGHT = 159

# 网页验证码滑块实际尺寸
WEB_SLIDER_IMAGE_WIDTH = 49
WEB_SLIDER_IMAGE_HEIGHT = 159


def _url2img(url):
    image = Image.open(io.BytesIO(base64.b64decode(url.split(",")[-1])))
    image_np = np.array(image)
    if image.mode == "RGB":
        image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    elif image.mode == "RGBA":
        image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGRA)
    else:
        image_cv = image_np

    return image_cv


def _generate_human_track(distance, total_time_ms=1205):
    """生成拟人化轨迹（加入加速曲线和随机扰动）"""
    track = []
    current_time = 0
    current_x = 0
    last_y = 0
    
    # 按下事件（加入初始抖动）
    track.append({
        "x": random.randint(-2, 1),
        "y": random.randint(-1.5, 1.5),
        "type": "down",
        "t": current_time
    })
    current_time += random.randint(10, 30)

    # 运动阶段划分（加速-匀速-减速）
    phases = [
        {'duration': 0.2, 'speed_ratio': 0.4},  # 加速阶段
        {'duration': 0.5, 'speed_ratio': 1.0},  # 匀速阶段
        {'duration': 0.3, 'speed_ratio': 0.3}   # 减速阶段
    ]
    
    # 计算各阶段参数
    phase_distances = []
    remaining = distance
    for phase in phases:
        phase_dist = int(remaining * phase['duration'])
        phase_distances.append(phase_dist)
        remaining -= phase_dist
    phase_distances[-1] += remaining  # 修正余数
    
    # 生成各阶段轨迹
    for phase_idx, phase_dist in enumerate(phase_distances):
        phase_speed = phases[phase_idx]['speed_ratio']
        step = 0
        
        while step < phase_dist:
            # 动态速度调整（加入随机扰动）
            speed_base = phase_speed * (1 + random.uniform(-0.1, 0.1))
            move_time = int(15 / (speed_base + 0.1))  # 时间间隔与速度成反比
            
            # 步长计算（基于贝塞尔曲线）
            progress = step / phase_dist
            if phase_idx == 0:  # 加速阶段
                step_size = int(3 + 5 * (1 - progress))
            elif phase_idx == 2:  # 减速阶段
                step_size = int(2 + 3 * progress)
            else:  # 匀速阶段
                step_size = random.randint(2, 4)
            
            # 边界保护
            step_size = min(step_size, phase_dist - step)
            if step_size <= 0:
                break
                
            current_x += step_size
            step += step_size
            
            # Y轴扰动（模拟手抖）
            y_move = last_y + random.randint(-2, 2)
            y_move = max(-3, min(3, y_move))  # 限制Y轴偏移范围
            last_y = y_move
            
            # 时间扰动
            current_time += move_time + random.randint(-5, 5)
            
            track.append({
                "x": current_x,
                "y": y_move,
                "type": "move",
                "t": current_time
            })
            
            # 随机暂停（模拟思考）
            if random.random() < 0.05:
                pause_time = random.randint(20, 50)
                current_time += pause_time

    # 终点微调（模拟校准动作）
    for _ in range(random.randint(1, 3)):
        current_x += random.choice([-1, 0, 1])
        current_x = max(0, min(current_x, distance))
        current_time += random.randint(10, 30)
        track.append({
            "x": current_x,
            "y": last_y + random.randint(-1, 1),
            "type": "move",
            "t": current_time
        })

    # 确保准确到达终点
    if current_x != distance:
        track.append({
            "x": distance,
            "y": 0,
            "type": "move",
            "t": current_time + 50
        })
    
    # 抬起事件（加入释放抖动）
    track.append({
        "x": distance + random.randint(-1, 1),
        "y": random.randint(-2, 2),
        "type": "up",
        "t": current_time + random.randint(30, 80)
    })
    
    # 后处理（时间对齐和偏移修正）
    total_time = track[-1]['t']
    time_scale = total_time_ms / total_time
    for point in track:
        point['t'] = int(point['t'] * time_scale)
        point['x'] = min(distance, max(0, point['x']))
        
    return track


def _parse_captcha_data(captcha_data):

    id = captcha_data["id"]
    bg_url = captcha_data["captcha"]["backgroundImage"]
    slider_url = captcha_data["captcha"]["sliderImage"]
    backgroundImageWidth = captcha_data["captcha"]["backgroundImageWidth"]
    backgroundImageHeight = captcha_data["captcha"]["backgroundImageHeight"]
    sliderImageWidth = captcha_data["captcha"]["sliderImageWidth"]
    sliderImageHeight = captcha_data["captcha"]["sliderImageHeight"]

    print(f"获取验证码成功 ID: {id}")
    print(f"背景图尺寸: {backgroundImageWidth}x{backgroundImageHeight}")
    print(f"滑块图尺寸: {sliderImageWidth}x{sliderImageHeight}")

    # 输出到文件
    # with open("captcha_data.json", "w") as f:
    #     json.dump(captcha_data, f, ensure_ascii=False, indent=4)

    # bg_url 和 slider_url 为 base64 编码的图片数据字符串
    bg = _url2img(bg_url)
    slider = _url2img(slider_url)

    return slider, bg

def solve_captcha(gen_response):

    response = gen_response
    if response.status_code != 200:
        raise Exception(f"获取验证码失败，状态码：{response.status_code}")
        
    captcha_data = response.json()

    # 1. 解析captcha的json数据
    slider, bg = _parse_captcha_data(captcha_data)

    # 2. 获取匹配结果
    solver = CaptchaMatcher()
    distance = solver.get_distance(slider, bg)
    print(f"滑块距离: {distance}")

    # 3. 考虑页面缩放比例
    scale =  WEB_BG_IMAGE_WIDTH / bg.shape[1]
    # print(f"页面缩放比例: {scale}")
    distance = int(distance * scale)

    # 4. 构造验证数据
    #     - Time: "2025-02-09T14:13:07.013Z"
    # random a time between 1.1s to 1.3s
    random.seed(time.time())
    track_time = random.randint(1200, 1300)
    track_list = _generate_human_track(distance, track_time)
    delta = track_list[-1]["t"]
    start_time = time.strftime("%Y-%m-%dT%H:%M:%S.601Z", time.gmtime())
    end_time = time.strftime("%Y-%m-%dT%H:%M:%S.720Z", time.gmtime(time.time() + delta / 1000))
    
    validation_data = {
        "bgImageHeight": WEB_BG_IMAGE_HEIGHT,
        "bgImageWidth": WEB_BG_IMAGE_WIDTH,
        "entSlidingTime": end_time,
        "sliderImageHeight": WEB_SLIDER_IMAGE_HEIGHT,
        "sliderImageWidth": WEB_SLIDER_IMAGE_WIDTH,
        "startSlidingTime": start_time,
        "trackList": track_list
    }
    
    # 5. 发送验证请求
    check_url = f"{SERVER_URL}/check"
    print(f"validation_data: {validation_data}")
    response = session.post(
        check_url,
        params={"id": captcha_data["id"]},
        json=validation_data,
        headers=HEADERS
    )
    
    # 6. 处理响应
    if response.status_code == 200:
        result = response.json()
        print(f"验证结果: {result}")
        return result, captcha_data

    else:
        print(f"验证请求失败，状态码：{response.status_code}")
        return False, captcha_data
    

# circular test
def test_captcha(session, test_times=100, test_gap=0.5, debug=False):
    test_times = test_times
    pass_count = 0

    false_path = "./.false_captcha"

    # firt clear the false path
    import os
    if os.path.exists(false_path):
        for file in os.listdir(false_path):
            os.remove(os.path.join(false_path, file))
    else:
        os.mkdir(false_path)


    for i in range(test_times):
        print(f"第 {i+1} 次测试")
        gen_url = f"{SERVER_URL}/gen"
        response = session.get(gen_url, headers=HEADERS)
        try_result, captcha_data = solve_captcha(response)
        if try_result:
            pass_count += 1
        else:
            # 将失败的验证码数据保存到文件(tranfer to png and jpg)
            slider, bg = _parse_captcha_data(captcha_data)
            slider_path = os.path.join(false_path, f"slider_{i}.png")
            bg_path = os.path.join(false_path, f"bg_{i}.jpg")
            cv2.imwrite(slider_path, slider)
            cv2.imwrite(bg_path, bg)

        time.sleep(test_gap) # 单位：S

    print(f"测试完成，通过率: {pass_count}/{test_times}")



if __name__ == "__main__":
    import requests
    from backpack.captchaSolver_legacy import CaptchaSolverEngine

    session = requests.Session()
    solver = CaptchaSolverEngine(session)
    # 可执行测试
    solver.test_captcha(test_times=100, test_gap=1.1)