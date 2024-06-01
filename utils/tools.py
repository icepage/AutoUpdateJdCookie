import base64
import cv2
import ddddocr
import io
import pyautogui
import random
import os
from PIL import Image, ImageGrab
import re
import time

def get_tmp_dir(tmp_dir:str = './tmp'):
    # 检查并创建 tmp 目录（如果不存在）
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    return tmp_dir


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


def get_ocr(**kwargs):
    return ddddocr.DdddOcr(show_ad=False, **kwargs)


def save_img(img_name, img_bytes):
    tmp_dir = get_tmp_dir()
    img_path = os.path.join(tmp_dir, f'{img_name}.png')
    # with open(img_path, 'wb') as file:
    #     file.write(img_bytes)
    # 使用 Pillow 打开图像
    with Image.open(io.BytesIO(img_bytes)) as img:
        # 保存图像到文件
        img.save(img_path)
    return img_path


def get_word(ocr, img_path):
    image_bytes = open(img_path, "rb").read()
    result = ocr.classification(image_bytes, png_fix=True)
    return result


def save_screenshot_img(left, top, right, bottom, img_name):
    tmp_dir = get_tmp_dir()
    img_path = os.path.join(tmp_dir, f'{img_name}.png')
    # 等待片刻以确保截图区域的准备
    time.sleep(2)

    # 获取屏幕截图
    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))

    # 保存截图
    screenshot.save(img_path)
    return img_path

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


def sort_rectangle_vertices(vertices):
    """
    获取左上、右上、右下、左下顺序的坐标
    """
    # 根据 y 坐标对顶点排序
    vertices = sorted(vertices, key=lambda x: x[1])

    # 根据 x 坐标对前两个和后两个顶点分别排序
    top_left, top_right = sorted(vertices[:2], key=lambda x: x[0])
    bottom_left, bottom_right = sorted(vertices[2:], key=lambda x: x[0])

    return [top_left, top_right, bottom_right, bottom_left]


def is_trapezoid(vertices):
    """
    判断四边形是否为梯形。
    vertices: 四个顶点按顺序排列的列表。
    返回值: 如果是梯形返回 True，否则返回 False。
    """
    top_width = abs(vertices[1][0] - vertices[0][0])
    bottom_width = abs(vertices[2][0] - vertices[3][0])
    return top_width < bottom_width


def get_shape_location_by_type(img_path, type: str):
    """
    获取指定形状在图片中的坐标
    """
    img = cv2.imread(img_path)
    imgGray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)  # 转灰度图
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)  # 高斯模糊
    imgCanny = cv2.Canny(imgBlur, 60, 60)  # Canny算子边缘检测
    contours, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 寻找轮廓点
    for obj in contours:
        perimeter = cv2.arcLength(obj, True)  # 计算轮廓周长
        approx = cv2.approxPolyDP(obj, 0.02 * perimeter, True)  # 获取轮廓角点坐标
        CornerNum = len(approx)  # 轮廓角点的数量
        x, y, w, h = cv2.boundingRect(approx)  # 获取坐标值和宽度、高度

        # 轮廓对象分类
        if CornerNum == 3:
            obj_type = "三角形"
        elif CornerNum == 4:
            if w == h:
                obj_type = "正方形"
            else:
                approx = sort_rectangle_vertices([vertex[0] for vertex in approx])
                if is_trapezoid(approx):
                    obj_type = "梯形"
                else:
                    obj_type = "长方形"
        elif CornerNum == 6:
            obj_type = "六边形"
        elif CornerNum == 20:
            obj_type = "五角星"
        elif 4 < CornerNum < 6 or 6 < CornerNum < 20 or CornerNum > 20:
            # 圆形
            obj_type = "圆形"
        else:
            obj_type = "未知"

        if obj_type == type:
            # 获取中心点
            center_x, center_y = x + w // 2, y + h // 2
            return center_x, center_y

    # 如果获取不到,则返回空
    return None, None


def click_by_autogui(x, y):
    """
    点击指定坐标的元素
    """
    # 移动鼠标到指定坐标
    pyautogui.moveTo(x, y)

    # 点击鼠标左键
    pyautogui.click()
