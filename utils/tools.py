import base64
import ddddocr
import pyautogui
import random
import re


def ddddocr_find_files_pic(target_file, background_file) -> int:
    """
    比对文件获取滚动长度
    """
    with open(target_file, 'rb') as f:
        target_bytes = f.read()
    with open(background_file, 'rb') as f:
        background_bytes = f.read()
    target = ddddocr_find_bytes_pic(target_bytes, background_bytes)
    return target


def ddddocr_find_bytes_pic(target_bytes, background_bytes) -> int:
    """
    比对bytes获取滚动长度
    """
    det = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    res = det.slide_match(target_bytes, background_bytes, simple_target=True)
    return res['target'][0]


def get_img_bytes(img_src: str) -> bytes:
    """
    获取图片的bytes
    """
    img_base64 = re.search(r'base64,(.*)', img_src)
    if img_base64:
        base64_code = img_base64.group(1)
        # print("提取的Base64编码:", base64_code)
        # 解码Base64字符串
        img_bytes = base64.b64decode(base64_code)
        return img_bytes
    else:
        raise "image is empty"


def slide_by_autogui(x, y, offset):
    """
    使用pyautogui实现滑块并自定义轨迹方程
    """
    xx = x + offset
    pyautogui.moveTo(x, y, duration=0.1)
    pyautogui.mouseDown()
    y += random.randint(9, 19)
    pyautogui.moveTo(x + int(offset * random.randint(15, 23) / 20), y, duration=0.28)
    y += random.randint(-9, 0)
    pyautogui.moveTo(x + int(offset * random.randint(17, 21) / 20), y, duration=random.randint(20, 31) / 100)
    y += random.randint(0, 8)
    pyautogui.moveTo(xx, y, duration=0.3)
    pyautogui.mouseUp()


def filter_forbidden_users(user_info: list, fields: list = None) -> list:
    """
    过滤出想要的字段的字典列表
    """
    return [{key: d[key] for key in fields if key in d} for d in user_info]


def get_forbidden_users_dict(users_list: list, user_datas: dict) -> dict:
    """
    获取用户phone:信息的列表
    """
    users_dict = {}
    for info in users_list:
        for key in user_datas:
            s = 'pt_pin=' + user_datas[key]['pt_pin']
            if s in info['value']:
                users_dict[key] = info
                break
    return users_dict


def base_move(slide_x_position, slide_y_position, small_img_bytes, background_img_bytes, slide_difference):
    """
    通用的识别滑块验证码的方法
    :param slide_x_position 滑块所在的x坐标
    :param slide_y_position 滑块所在的y坐标
    :param small_img_bytes 小图的base64
    :param background_img_bytes 背景图的base64
    :param slide_difference 偏移量，根据实际情况调节
    """

    # 获取滑动长度
    x = ddddocr_find_bytes_pic(small_img_bytes, background_img_bytes) + slide_difference

    slide_by_autogui(slide_x_position, slide_y_position, x)
