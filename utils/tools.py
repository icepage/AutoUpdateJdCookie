import aiohttp
import asyncio
import base64
import cv2
import ddddocr
from enum import Enum
import io
from loguru import logger
import numpy as np
import random
import os
from PIL import Image
import re
from typing import Dict, Any
from utils.consts import supported_colors
from typing import Union, List

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
            user_pt_pin = user_datas[key]['pt_pin']
            if user_pt_pin == extract_pt_pin(info['value']):
                users_dict[key] = info
                break
    return users_dict


async def human_like_mouse_move(page, from_x, to_x, y):
    """
    移动鼠标
    """
    # 第一阶段：快速移动到目标附近，耗时 0.28 秒
    fast_duration = 0.28
    fast_steps = 50
    fast_target_x = from_x + (to_x - from_x) * 0.8
    fast_dx = (fast_target_x - from_x) / fast_steps

    for _ in range(fast_steps):
        from_x += fast_dx
        await page.mouse.move(from_x, y)
        await asyncio.sleep(fast_duration / fast_steps)

    # 第二阶段：稍微慢一些，耗时随机 20 到 31 毫秒
    slow_duration = random.randint(20, 31) / 1000
    slow_steps = 10
    slow_target_x = from_x + (to_x - from_x) * 0.9
    slow_dx = (slow_target_x - from_x) / slow_steps

    for _ in range(slow_steps):
        from_x += slow_dx
        await page.mouse.move(from_x, y)
        await asyncio.sleep(slow_duration / slow_steps)

    # 第三阶段：缓慢移动到目标位置，耗时 0.3 秒
    final_duration = 0.3
    final_steps = 20
    final_dx = (to_x - from_x) / final_steps

    for _ in range(final_steps):
        from_x += final_dx
        await page.mouse.move(from_x, y)
        await asyncio.sleep(final_duration / final_steps)


async def solve_slider_captcha(page, slider, distance, slide_difference):
    """
    解决移动滑块
    """
    # 等待滑块元素出现
    box = await slider.bounding_box()

    # 计算滑块的中心坐标
    from_x = box['x'] + box['width'] / 2
    to_y = from_y = box['y'] + box['height'] / 2

    # 模拟按住滑块
    await page.mouse.move(from_x, from_y)
    await page.mouse.down()

    to_x = from_x + distance + slide_difference
    # 平滑移动到目标位置
    await human_like_mouse_move(page, from_x, to_x, to_y)

    # 放开滑块
    await page.mouse.up()


async def new_solve_slider_captcha(page, slider, distance, slide_difference):
    # 等待滑块元素出现
    distance = distance + slide_difference
    box = await slider.bounding_box()
    await page.mouse.move(box['x'] + 10 , box['y'] + 10)
    await page.mouse.down()  # 模拟鼠标按下
    await page.mouse.move(box['x'] + distance + random.uniform(8, 10), box['y'], steps=5)  # 模拟鼠标拖动，考虑到实际操作中可能存在的轻微误差和波动，加入随机偏移量
    await asyncio.sleep(random.randint(1, 5) / 10)  # 随机等待一段时间，模仿人类操作的不确定性
    await page.mouse.move(box['x'] + distance, box['y'], steps=10)  # 继续拖动滑块到目标位置
    await page.mouse.up()  # 模拟鼠标释放，完成滑块拖动
    await asyncio.sleep(3)  # 等待3秒，等待滑块验证结果

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
        elif CornerNum == 8:
            obj_type = "圆形"
        elif CornerNum == 20:
            obj_type = "五角星"
        else:
            obj_type = "未知"

        if obj_type == type:
            # 获取中心点
            center_x, center_y = x + w // 2, y + h // 2
            return center_x, center_y

    # 如果获取不到,则返回空
    return None, None


def get_shape_location_by_color(img_path, target_color):
    """
    根据颜色获取指定形状在图片中的坐标
    """

    # 读取图像
    image = cv2.imread(img_path)
    # 读取图像并转换为 HSV 色彩空间。
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 获取目标颜色的范围
    lower, upper = supported_colors[target_color]
    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")

    # 创建掩码并找到轮廓
    mask = cv2.inRange(hsv_image, lower, upper)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 遍历轮廓并在中心点画点
    for contour in contours:
        # 过滤掉太小的区域
        if cv2.contourArea(contour) > 100:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                return cX, cY

    return None, None


def rgba2rgb(img_name, rgba_img_path, tmp_dir: str = './tmp'):
    """
    rgba图片转rgb
    """
    tmp_dir = get_tmp_dir(tmp_dir=tmp_dir)

    # 打开一个带透明度的RGBA图像
    rgba_image = Image.open(rgba_img_path)
    # 创建一个白色背景图像
    rgb_image = Image.new("RGB", rgba_image.size, (255, 255, 255))
    # 将RGBA图像粘贴到背景图像上，使用透明度作为蒙版
    rgb_image.paste(rgba_image, (0, 0), rgba_image)

    rgb_image_path = os.path.join(tmp_dir, f"{img_name}.png")
    rgb_image.save(rgb_image_path)

    return rgb_image_path


class SendType(Enum):
    success = 0
    fail = 1


async def send_call_method(obj, method_name, *args, **kwargs):
    """
    使用反射调用发送消息的方法。

    :param obj: 对象实例
    :param method_name: 方法名称
    :param args: 位置参数
    :param kwargs: 关键字参数
    :return: 方法的返回值
    """
    # 检查对象是否具有指定的方法
    if hasattr(obj, method_name):
        method = getattr(obj, method_name)
        # 检查获取的属性是否是可调用的
        return await method(*args, **kwargs)


async def send_msg(send_api, send_type: int, msg: str):
    """
    读取配置文件，调用send_call_method发消息
    """
    from config import is_send_msg
    if not is_send_msg:
        return

    from config import send_info, is_send_success_msg, is_send_fail_msg
    if (send_type == SendType.success.value and is_send_success_msg) or (send_type == SendType.fail.value and is_send_fail_msg):
        for key in send_info:
            for url in send_info[key]:
                rep = await send_call_method(send_api, key, url, msg)
                logger.info(f"发送消息到 {url}, 响应:{rep}")

    return


def get_zero_or_not(v):
    if v < 0:
        return 0
    return v


def expand_coordinates(x1, y1, x2, y2, N):
    # Calculate expanded coordinates
    new_x1 = get_zero_or_not(x1 - N)
    new_y1 = get_zero_or_not(y1 - N)
    new_x2 = x2 + N
    new_y2 = y2 + N
    return new_x1, new_y1, new_x2, new_y2


def cv2_save_img(img_name, img, tmp_dir:str = './tmp'):
    tmp_dir = get_tmp_dir(tmp_dir)
    img_path = os.path.join(tmp_dir, f'{img_name}.png')
    cv2.imwrite(img_path, img)
    return img_path


async def send_request(url: str, method: str, headers: Dict[str, Any], data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
    """
    发请求的通用方法
    """
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url=url, json=data, headers=headers, **kwargs) as response:
            return await response.json()


def validate_proxy_config(proxy):
    """
    验证 server 是否为有效的 URL 地址
    """
    server = proxy.get("server")
    # 排除缺省值
    if server == "http://":
        return True, "未配置代理"

    username = proxy.get("username")
    password = proxy.get("password")

    # 使用正则表达式来检查 server 是否是有效的 URL
    url_pattern = re.compile(
        r'^(http|https|socks5)://'
        r'(?:(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,6}|'  # 域名
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'    # 或者IP地址
        r'(?::\d+)?'                              # 可选端口
        r'(?:/.*)?$'                              # 可选路径
    )

    if not server or not url_pattern.match(server):
        return False, "代理的server URL异常"

    # 检查 username 是否为空，若为空则忽略 password 的检查
    if username:
        if not password:
            return False, "代理只有账号, 缺少密码配置"
    else:
        if password:
            return False, "代理只有密码, 缺少账号配置"

    return True, "代理配置正常可用"


def is_valid_verification_code(code: str):
    """
    判断验证码格式是否正确
    """
    return bool(re.match(r"^\d{6}$", code))


def extract_pt_pin(value: str) -> Union[str, None]:
    """
    用正则提取value中pt_pin的值, 返回一个pt_pin,如果返回多个或没匹配上则返回空, 支持以下几种格式:
    pt_key=xxx;pt_pin=xxx;
    pt_key=xxx;pt_pin="xxx";
    pt_key=xxx;pt_pin='xxx';
    pt_pin=xxx;pt_key=xxx;
    pt_pin=xxx;pt_key="xxx";
    pt_pin=xxx;pt_key='xxx';
    """
    pattern = r'pt_pin\s*=\s*(["\']?)([^"\';]+)\1'  # 捕获 pt_pin 的值，并匹配可能的引号
    matches = re.findall(pattern, value)
    # 如果找到了多个匹配或没有匹配，则返回空
    if len(matches) == 1:
        # 返回 pt_pin 的值
        return matches[0][1]
    return None


def filter_cks(
    env_data: List[Dict[str, Any]],
    *,
    status: int = None,
    id: int = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    过滤env_data中符合条件的字典。

    :param env_data: ql环境变量数据
    :param status: 过滤条件之一，status字段的值。
    :param id: 过滤条件之一，id字段的值。
    :param kwargs: 其他过滤条件。
    :return: 符合条件的字典列表。
    """
    # 检查必传参数是否至少传了一个
    if status is None and id is None and not kwargs:
        raise ValueError("至少需要传入一个过滤条件（status、id或其他字段）。")

    # 合并所有过滤条件
    filters = {}
    if status is not None:
        filters["status"] = status
    if id is not None:
        filters["id"] = id
    # 添加其他过滤条件
    filters.update(kwargs)

    # 过滤数据
    filtered_list = []

    for item in env_data:
        if all(item.get(key) == value for key, value in filters.items()):
            filtered_list.append(item)

    return filtered_list


def desensitize_account(account, enable_desensitize=True):
    """
    对传入的账号（QQ号或手机号）进行脱敏处理
    :param account: 账号（QQ号或手机号）
    :param enable_desensitize: 是否开启脱敏，默认为 True
    :return: 脱敏后的账号或原账号
    """
    if not account or not enable_desensitize:
        # 如果账号为空或脱敏未开启，直接返回原账号
        return account

    # 判断是否为手机号（假设手机号为11位数字）
    if account.isdigit() and len(account) == 11:
        # 手机号脱敏：前3后4，中间4位用*代替
        return account[:3] + '****' + account[-4:]

    # 判断是否为QQ号（假设QQ号为5位以上数字）
    if account.isdigit() and len(account) >= 5:
        # QQ号脱敏：前2后2，中间用*代替
        return account[:2] + '***' + account[-2:]

    # 如果不是手机号或QQ号，直接返回原账号
    return account

def sanitize_header_value(value: str) -> str:
    """
    清除 HTTP 头部值中的换行符，防止 header 注入
    """
    return value.replace('\n', '').replace('\r', '').strip()
