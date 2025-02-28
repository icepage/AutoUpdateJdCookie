import aiohttp
import argparse
import asyncio
from api.qinglong import QlApi, QlOpenApi
from api.send import SendApi
from utils.ck import get_invalid_ck_ids
from config import (
    qinglong_data,
    user_datas,
)
import cv2
import json
from loguru import logger
import os
from playwright.async_api import Playwright, async_playwright
from playwright._impl._errors import TimeoutError
import random
import re
from PIL import Image  # 用于图像处理
import traceback
from typing import Union
from utils.consts import (
    jd_login_url,
    supported_types,
    supported_colors,
    supported_sms_func
)
from utils.tools import (
    get_tmp_dir,
    get_img_bytes,
    get_forbidden_users_dict,
    filter_forbidden_users,
    save_img,
    get_ocr,
    get_word,
    get_shape_location_by_type,
    get_shape_location_by_color,
    rgba2rgb,
    send_msg,
    new_solve_slider_captcha,
    ddddocr_find_files_pic,
    expand_coordinates,
    cv2_save_img,
    ddddocr_find_bytes_pic,
    solve_slider_captcha,
    validate_proxy_config,
    is_valid_verification_code,
    filter_cks,
    extract_pt_pin
)

"""
基于playwright做的
"""
logger.add(
    sink="main.log",
    level="DEBUG"
)


async def download_image(url, filepath):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(filepath, 'wb') as f:
                    f.write(await response.read())
                print(f"Image downloaded to {filepath}")
            else:
                print(f"Failed to download image. Status code: {response.status}")


async def check_notice(page):
    try:
        logger.info("检查登录是否报错")
        notice = await page.wait_for_function(
            """
            () => {
                const notice = document.querySelectorAll('.notice')[1];
                return notice && notice.textContent.trim() !== '' ? notice.textContent.trim() : false;
            }
            """,
            timeout = 3000
        )
        raise RuntimeError(notice)
    except TimeoutError:
        logger.info("登录未发现报错")
        return

async def auto_move_slide_v2(page, retry_times: int = 2, slider_selector: str = 'img.move-img', move_solve_type: str = ""):
    for i in range(retry_times):
        logger.info(f'第{i + 1}次开启滑块验证')
        # 查找小图
        try:
            # 查找小图
            await page.wait_for_selector('.captcha_drop', state='visible', timeout=3000)
        except Exception as e:
            logger.info('未找到验证码框, 退出滑块验证')
            return
        await auto_move_slide(page, retry_times=5, slider_selector = slider_selector, move_solve_type = move_solve_type)

        # 判断是否一次过了滑块
        captcha_drop_visible = await page.is_visible('.captcha_drop')

        # 存在就重新滑一次
        if captcha_drop_visible:
            if i == retry_times - 1:
                return
            logger.info('一次过滑块失败, 再次尝试滑块验证')
            await page.wait_for_selector('.captcha_drop', state='visible', timeout=3000)
            # 点外键
            sign_locator = page.locator('#header').locator('.text-header')
            sign_locator_box = await sign_locator.bounding_box()
            sign_locator_left_x = sign_locator_box['x']
            sign_locator_left_y = sign_locator_box['y']
            await page.mouse.click(sign_locator_left_x, sign_locator_left_y)
            await asyncio.sleep(1)
            # 提交键
            submit_locator = page.locator('.btn.J_ping.active')
            await submit_locator.click()
            await asyncio.sleep(1)
            continue
        return

async def auto_move_slide(page, retry_times: int = 2, slider_selector: str = 'img.move-img', move_solve_type: str = ""):
    """
    自动识别移动滑块验证码
    """
    for i in range(retry_times):
        logger.info(f'第{i + 1}次尝试自动移动滑块中...')
        try:
            # 查找小图
            await page.wait_for_selector('#small_img', state='visible', timeout=3000)
        except Exception as e:
            # 未找到元素，认为成功，退出循环
            logger.info('未找到小图,退出移动滑块')
            break

        # 获取 src 属性
        small_src = await page.locator('#small_img').get_attribute('src')
        background_src = await page.locator('#cpc_img').get_attribute('src')

        # 获取 bytes
        small_img_bytes = get_img_bytes(small_src)
        background_img_bytes = get_img_bytes(background_src)

        # 保存小图
        small_img_path = save_img('small_img', small_img_bytes)
        small_img_width = await page.evaluate('() => { return document.getElementById("small_img").clientWidth; }')  # 获取网页的图片尺寸
        small_img_height = await page.evaluate('() => { return document.getElementById("small_img").clientHeight; }')  # 获取网页的图片尺寸
        small_image = Image.open(small_img_path)  # 打开图像
        resized_small_image = small_image.resize((small_img_width, small_img_height))  # 调整图像尺寸
        resized_small_image.save(small_img_path)  # 保存调整后的图像

        # 保存大图
        background_img_path = save_img('background_img', background_img_bytes)
        background_img_width = await page.evaluate('() => { return document.getElementById("cpc_img").clientWidth; }')  # 获取网页的图片尺寸
        background_img_height = await page.evaluate('() => { return document.getElementById("cpc_img").clientHeight; }')  # 获取网页的图片尺寸
        background_image = Image.open(background_img_path)  # 打开图像
        resized_background_image = background_image.resize((background_img_width, background_img_height))  # 调整图像尺寸
        resized_background_image.save(background_img_path)  # 保存调整后的图像

        # 获取滑块
        slider = page.locator(slider_selector)
        await asyncio.sleep(1)

        # 这里是一个标准算法偏差
        slide_difference = 10

        if move_solve_type == "old":
            # 用于调试
            distance = ddddocr_find_bytes_pic(small_img_bytes, background_img_bytes)
            await asyncio.sleep(1)
            await solve_slider_captcha(page, slider, distance, slide_difference)
            await asyncio.sleep(1)
            continue
        # 获取要移动的长度
        distance = ddddocr_find_files_pic(small_img_path, background_img_path)
        await asyncio.sleep(1)
        # 移动滑块
        await new_solve_slider_captcha(page, slider, distance, slide_difference)
        await asyncio.sleep(1)


async def auto_shape(page, retry_times: int = 5):
    # 图像识别
    ocr = get_ocr(beta=True)
    # 文字识别
    det = get_ocr(det=True)
    # 自己训练的ocr, 提高文字识别度
    my_ocr = get_ocr(det=False, ocr=False, import_onnx_path="myocr_v1.onnx", charsets_path="charsets.json")
    """
    自动识别滑块验证码
    """
    for i in range(retry_times):
        logger.info(f'第{i + 1}次自动识别形状中...')
        try:
            # 查找小图
            await page.wait_for_selector('div.captcha_footer img', state='visible', timeout=3000)
        except Exception as e:
            # 未找到元素，认为成功，退出循环
            logger.info('未找到形状图,退出识别状态')
            break

        tmp_dir = get_tmp_dir()

        background_img_path = os.path.join(tmp_dir, f'background_img.png')
        # 获取大图元素
        background_locator = page.locator('#cpc_img')
        # 获取元素的位置和尺寸
        backend_bounding_box = await background_locator.bounding_box()
        backend_top_left_x = backend_bounding_box['x']
        backend_top_left_y = backend_bounding_box['y']

        # 截取元素区域
        await page.screenshot(path=background_img_path, clip=backend_bounding_box)

        # 获取 图片的src 属性和button按键
        word_img_src = await page.locator('div.captcha_footer img').get_attribute('src')
        button = page.locator('div.captcha_footer button#submit-btn')

        # 找到刷新按钮
        refresh_button = page.locator('.jcap_refresh')


        # 获取文字图并保存
        word_img_bytes = get_img_bytes(word_img_src)
        rgba_word_img_path = save_img('rgba_word_img', word_img_bytes)

        # 文字图是RGBA的，有蒙板识别不了，需要转成RGB
        rgb_word_img_path = rgba2rgb('rgb_word_img', rgba_word_img_path)

        # 获取问题的文字
        word = get_word(ocr, rgb_word_img_path)

        if word.find('色') > 0:
            target_color = word.split('请选出图中')[1].split('的图形')[0]
            if target_color in supported_colors:
                logger.info(f'正在点击中......')
                # 获取点的中心点
                center_x, center_y = get_shape_location_by_color(background_img_path, target_color)
                if center_x is None and center_y is None:
                    logger.info(f'识别失败,刷新中......')
                    await refresh_button.click()
                    await asyncio.sleep(random.uniform(2, 4))
                    continue
                # 得到网页上的中心点
                x, y = backend_top_left_x + center_x, backend_top_left_y + center_y
                # 点击图片
                await page.mouse.click(x, y)
                await asyncio.sleep(random.uniform(1, 4))
                # 点击确定
                await button.click()
                await asyncio.sleep(random.uniform(2, 4))
                continue
            else:
                logger.info(f'不支持{target_color},刷新中......')
                # 刷新
                await refresh_button.click()
                await asyncio.sleep(random.uniform(2, 4))
                continue

        # 这里是文字验证码了
        elif word.find('依次') > 0:
            logger.info(f'开始文字识别,点击中......')
            # 获取文字的顺序列表
            try:
                target_char_list = list(re.findall(r'[\u4e00-\u9fff]+', word)[1])
            except IndexError:
                logger.info(f'识别文字出错,刷新中......')
                await refresh_button.click()
                await asyncio.sleep(random.uniform(2, 4))
                continue

            target_char_len = len(target_char_list)

            # 识别字数不对
            if target_char_len < 4:
                logger.info(f'识别的字数小于4,刷新中......')
                await refresh_button.click()
                await asyncio.sleep(random.uniform(2, 4))
                continue

            # 取前4个的文字
            target_char_list = target_char_list[:4]

            # 定义【文字, 坐标】的列表
            target_list = [[x, []] for x in target_char_list]

            # 获取大图的二进制
            background_locator = page.locator('#cpc_img')
            background_locator_src = await background_locator.get_attribute('src')
            background_locator_bytes = get_img_bytes(background_locator_src)
            bboxes = det.detection(background_locator_bytes)

            count = 0
            im = cv2.imread(background_img_path)
            for bbox in bboxes:
                # 左上角
                x1, y1, x2, y2 = bbox
                # 做了一下扩大
                expanded_x1, expanded_y1, expanded_x2, expanded_y2 = expand_coordinates(x1, y1, x2, y2, 10)
                im2 = im[expanded_y1:expanded_y2, expanded_x1:expanded_x2]
                img_path = cv2_save_img('word', im2)
                image_bytes = open(img_path, "rb").read()
                result = my_ocr.classification(image_bytes)
                if result in target_char_list:
                    for index, target in enumerate(target_list):
                        if result == target[0] and target[0] is not None:
                            x = x1 + (x2 - x1) / 2
                            y = y1 + (y2 - y1) / 2
                            target_list[index][1] = [x, y]
                            count += 1

            if count != target_char_len:
                logger.info(f'文字识别失败,刷新中......')
                await refresh_button.click()
                await asyncio.sleep(random.uniform(2, 4))
                continue

            await asyncio.sleep(random.uniform(0, 1))
            try:
                for char in target_list:
                    center_x = char[1][0]
                    center_y = char[1][1]
                    # 得到网页上的中心点
                    x, y = backend_top_left_x + center_x, backend_top_left_y + center_y
                    # 点击图片
                    await page.mouse.click(x, y)
                    await asyncio.sleep(random.uniform(1, 4))
            except IndexError:
                logger.info(f'识别文字出错,刷新中......')
                await refresh_button.click()
                await asyncio.sleep(random.uniform(2, 4))
                continue
            # 点击确定
            await button.click()
            await asyncio.sleep(random.uniform(2, 4))

        else:
            shape_type = word.split('请选出图中的')[1]
            if shape_type in supported_types:
                logger.info(f'已找到图形,点击中......')
                if shape_type == "圆环":
                    shape_type = shape_type.replace('圆环', '圆形')
                # 获取点的中心点
                center_x, center_y = get_shape_location_by_type(background_img_path, shape_type)
                if center_x is None and center_y is None:
                    logger.info(f'识别失败,刷新中......')
                    await refresh_button.click()
                    await asyncio.sleep(random.uniform(2, 4))
                    continue
                # 得到网页上的中心点
                x, y = backend_top_left_x + center_x, backend_top_left_y + center_y
                # 点击图片
                await page.mouse.click(x, y)
                await asyncio.sleep(random.uniform(1, 4))
                # 点击确定
                await button.click()
                await asyncio.sleep(random.uniform(2, 4))
                continue
            else:
                logger.info(f'不支持{shape_type},刷新中......')
                # 刷新
                await refresh_button.click()
                await asyncio.sleep(random.uniform(2, 4))
                continue


async def sms_recognition(page, user, mode):
    try:
        from config import sms_func
    except ImportError:
        sms_func = "no"

    sms_func = user_datas[user].get("sms_func", sms_func)

    if sms_func not in supported_sms_func:
        raise Exception(f"sms_func只支持{supported_sms_func}")

    if mode == "cron" and sms_func == "manual_input":
        sms_func = "no"

    if sms_func == "no":
        raise Exception("sms_func为no关闭, 跳过短信验证码识别环节")

    logger.info('点击【获取验证码】中')
    await page.click('button.getMsg-btn')
    await asyncio.sleep(1)
    # 自动识别滑块
    await auto_move_slide(page, retry_times=5, slider_selector='div.bg-blue')
    await auto_shape(page, retry_times=30)

    # 识别是否成功发送验证码
    await page.wait_for_selector('button.getMsg-btn:has-text("重新发送")', timeout=3000)
    logger.info("发送短信验证码成功")

    # 手动输入
    # 用户在60S内，手动在终端输入验证码
    if sms_func == "manual_input":
        from inputimeout import inputimeout, TimeoutOccurred
        try:
            verification_code = inputimeout(prompt="请输入验证码：", timeout=60)
        except TimeoutOccurred:
            return

    # 通过调用web_hook的方式来实现全自动输入验证码
    elif sms_func == "webhook":
        from utils.tools import send_request
        try:
            from config import sms_webhook
        except ImportError:
            sms_webhook = ""
        sms_webhook = user_datas[user].get("sms_webhook", sms_webhook)

        if sms_webhook is None:
            raise Exception(f"sms_webhook未配置")

        headers = {
            'Content-Type': 'application/json',
        }
        data = {"phone_number": user}
        response = await send_request(url=sms_webhook, method="post", headers=headers, data=data)
        verification_code = response['data']['code']

    await asyncio.sleep(1)
    if not is_valid_verification_code(verification_code):
        logger.error(f"验证码需为6位数字, 输入的验证码为{verification_code}, 异常")
        raise Exception(f"验证码异常")

    logger.info('填写验证码中...')
    verification_code_input = page.locator('input.acc-input.msgCode')
    for v in verification_code:
        await verification_code_input.type(v, no_wait_after=True)
        await asyncio.sleep(random.random() / 10)

    logger.info('点击提交中...')
    await page.click('a.btn')


async def voice_verification(page, user, mode):
    from utils.consts import supported_voice_func
    try:
        from config import voice_func
    except ImportError:
        voice_func = "no"

    voice_func = user_datas[user].get("voice_func", voice_func)

    if voice_func not in supported_voice_func:
        raise Exception(f"voice_func只支持{supported_voice_func}")

    if mode == "cron" and voice_func == "manual_input":
        voice_func = "no"

    if voice_func == "no":
        raise Exception("voice_func为no关闭, 跳过手机语音识别")

    logger.info('点击获取验证码中')
    await page.click('button.getMsg-btn:has-text("点击获取验证码")')
    await asyncio.sleep(1)
    # 自动识别滑块
    await auto_move_slide(page, retry_times=5, slider_selector='div.bg-blue')
    await auto_shape(page, retry_times=30)

    # 识别是否成功发送验证码
    await page.wait_for_selector('button.getMsg-btn:has-text("重新发送")', timeout=3000)
    logger.info("发送手机语音识别验证码成功")

    # 手动输入
    # 用户在60S内，手动在终端输入验证码
    if voice_func == "manual_input":
        from inputimeout import inputimeout, TimeoutOccurred
        try:
            verification_code = inputimeout(prompt="请输入验证码：", timeout=60)
        except TimeoutOccurred:
            return

    await asyncio.sleep(1)
    if not is_valid_verification_code(verification_code):
        logger.error(f"验证码需为6位数字, 输入的验证码为{verification_code}, 异常")
        raise Exception(f"验证码异常")

    logger.info('填写验证码中...')
    verification_code_input = page.locator('input.acc-input.msgCode')
    for v in verification_code:
        await verification_code_input.type(v, no_wait_after=True)
        await asyncio.sleep(random.random() / 10)

    logger.info('点击提交中...')
    await page.click('a.btn')


async def get_jd_pt_key(playwright: Playwright, user, mode) -> Union[str, None]:
    """
    获取jd的pt_key
    """

    try:
        from config import headless
    except ImportError:
        headless = False

    args = '--no-sandbox', '--disable-setuid-sandbox', '--disable-software-rasterizer', '--disable-gpu'

    try:
        # 引入代理
        from config import proxy
        # 检查代理的配置
        is_proxy_valid, msg = validate_proxy_config(proxy)
        if not is_proxy_valid:
            logger.error(msg)
            proxy = None
        if msg == "未配置代理":
            logger.info(msg)
            proxy = None
    except ImportError:
        logger.info("未配置代理")
        proxy = None

    browser = await playwright.chromium.launch(headless=headless, args=args, proxy=proxy)
    try:
        # 引入UA
        from config import user_agent
    except ImportError:
        from utils.consts import user_agent
    context = await browser.new_context(user_agent=user_agent)

    try:
        page = await context.new_page()
        await page.set_viewport_size({"width": 360, "height": 640})
        await page.goto(jd_login_url)

        if user_datas[user].get("user_type") == "qq":
            await page.get_by_role("checkbox").check()
            await asyncio.sleep(1)
            # 点击QQ登录
            await page.locator("a.quick-qq").click()
            await asyncio.sleep(1)

            # 等待 iframe 加载完成
            await page.wait_for_selector("#ptlogin_iframe")
            # 切换到 iframe
            iframe = page.frame(name="ptlogin_iframe")

            # 通过 id 选择 "密码登录" 链接并点击
            await iframe.locator("#switcher_plogin").click()
            await asyncio.sleep(1)
            # 填写账号
            username_input = iframe.locator("#u")  # 替换为实际的账号
            for u in user:
                await username_input.type(u, no_wait_after=True)
                await asyncio.sleep(random.random() / 10)
            await asyncio.sleep(1)
            # 填写密码
            password_input = iframe.locator("#p")  # 替换为实际的密码
            password = user_datas[user]["password"]
            for p in password:
                await password_input.type(p, no_wait_after=True)
                await asyncio.sleep(random.random() / 10)
            await asyncio.sleep(1)
            # 点击登录按钮
            await iframe.locator("#login_button").click()
            await asyncio.sleep(1)
            # 这里检测安全验证
            new_vcode_area = iframe.locator("div#newVcodeArea")
            style = await new_vcode_area.get_attribute("style")
            if style and "display: block" in style:
                if await new_vcode_area.get_by_text("安全验证").text_content() == "安全验证":
                    logger.error(f"QQ号{user}需要安全验证, 登录失败，请使用其它账号类型")
                    raise Exception(f"QQ号{user}需要安全验证, 登录失败，请使用其它账号类型")

        else:
            await page.get_by_text("账号密码登录").click()

            username_input = page.locator("#username")
            for u in user:
                await username_input.type(u, no_wait_after=True)
                await asyncio.sleep(random.random() / 10)

            password_input = page.locator("#pwd")
            password = user_datas[user]["password"]
            for p in password:
                await password_input.type(p, no_wait_after=True)
                await asyncio.sleep(random.random() / 10)

            await asyncio.sleep(random.random())
            await page.locator('.policy_tip-checkbox').click()
            await asyncio.sleep(random.random())
            await page.locator('.btn.J_ping.active').click()

            # 自动识别移动滑块验证码
            await asyncio.sleep(1)
            await auto_move_slide_v2(page, retry_times=5)

            # 自动验证形状验证码
            await asyncio.sleep(1)
            await auto_shape(page, retry_times=30)

            # 进行短信验证识别
            await asyncio.sleep(1)
            if await page.locator('text="手机短信验证"').count() != 0:
                logger.info("开始短信验证码识别环节")
                await sms_recognition(page, user, mode)

            # 进行手机语音验证识别
            if await page.locator('div#header .text-header:has-text("手机语音验证")').count() > 0:
                logger.info("检测到手机语音验证页面,开始识别")
                await voice_verification(page, user, mode)

            # 检查警告,如账号存在风险或账密不正确等
            await check_notice(page)

        # 等待验证码通过
        logger.info("等待获取cookie...")
        await page.wait_for_selector('#msShortcutMenu', state='visible', timeout=120000)

        cookies = await context.cookies()
        for cookie in cookies:
            if cookie['name'] == 'pt_key':
                pt_key = cookie["value"]
                return pt_key

        return None

    except Exception as e:
        traceback.print_exc()
        return None

    finally:
        await context.close()
        await browser.close()


async def get_ql_api(ql_data):
    """
    封装了QL的登录
    """
    logger.info("开始获取QL登录态......")

    # 优化client_id和client_secret
    client_id = ql_data.get('client_id')
    client_secret = ql_data.get('client_secret')
    if client_id and client_secret:
        logger.info("使用client_id和client_secret登录......")
        qlapi = QlOpenApi(ql_data["url"])
        response = await qlapi.login(client_id=client_id, client_secret=client_secret)
        if response['code'] == 200:
            logger.info("client_id和client_secret正常可用......")
            return qlapi
        else:
            logger.info("client_id和client_secret异常......")

    qlapi = QlApi(ql_data["url"])

    # 其次用token
    token = ql_data.get('token')
    if token:
        logger.info("已设置TOKEN,开始检测TOKEN状态......")
        qlapi.login_by_token(token)

        # 如果token失效，就用账号密码登录
        response = await qlapi.get_envs()
        if response['code'] == 401:
            logger.info("Token已失效, 正使用账号密码获取QL登录态......")
            response = await qlapi.login_by_username(ql_data.get("username"), ql_data.get("password"))
            if response['code'] != 200:
                logger.error(f"账号密码登录失败. response: {response}")
                raise Exception(f"账号密码登录失败. response: {response}")
        else:
            logger.info("Token正常可用......")
    else:
        # 最后用账号密码
        logger.info("正使用账号密码获取QL登录态......")
        response = await qlapi.login_by_username(ql_data.get("username"), ql_data.get("password"))
        if response['code'] != 200:
            logger.error(f"账号密码登录失败. response: {response}")
            raise Exception(f"账号密码登录失败.response: {response}")
    return qlapi


async def main(mode: str = None):
    """
    :param mode 运行模式, 当mode = cron时，sms_func为 manual_input时，将自动传成no
    """
    try:
        qlapi = await get_ql_api(qinglong_data)
        send_api = SendApi("ql")
        # 拿到禁用的用户列表
        response = await qlapi.get_envs()
        if response['code'] == 200:
            logger.info("获取环境变量成功")
        else:
            logger.error(f"获取环境变量失败， response: {response}")
            raise Exception(f"获取环境变量失败， response: {response}")

        env_data = response['data']
        # 获取值为JD_COOKIE的环境变量
        jd_ck_env_datas = filter_cks(env_data, name='JD_COOKIE')
        # 从value中过滤出pt_pin, 注意只支持单行单pt_pin
        jd_ck_env_datas = [ {**x, 'pt_pin': extract_pt_pin(x['value'])} for x in jd_ck_env_datas if extract_pt_pin(x['value'])]

        try:
            logger.info("检测CK任务开始")
            # 先获取启用中的env_data
            up_jd_ck_list = filter_cks(jd_ck_env_datas, status=0, name='JD_COOKIE')
            # 这一步会去检测这些JD_COOKIE
            invalid_cks_id_list = await get_invalid_ck_ids(up_jd_ck_list)
            if invalid_cks_id_list:
                # 禁用QL的失效环境变量
                ck_ids_datas = bytes(json.dumps(invalid_cks_id_list), 'utf-8')
                await qlapi.envs_disable(data=ck_ids_datas)
                # 更新jd_ck_env_datas
                jd_ck_env_datas = [{**x, 'status': 1} if x.get('id') in invalid_cks_id_list or x.get('_id') in invalid_cks_id_list else x for x in jd_ck_env_datas]
            logger.info("检测CK任务完成")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"检测CK任务失败, 跳过检测, 报错原因为{e}")

        # 获取需强制更新pt_pin
        force_update_pt_pins = [user_datas[key]["pt_pin"] for key in user_datas if user_datas[key].get("force_update") is True]
        # 获取禁用和需要强制更新的users
        forbidden_users = [x for x in jd_ck_env_datas if (x['status'] == 1 or x['pt_pin'] in force_update_pt_pins)]

        if not forbidden_users:
            logger.info("所有COOKIE环境变量正常，无需更新")
            return

        # 获取需要的字段
        filter_users_list = filter_forbidden_users(forbidden_users, ['_id', 'id', 'value', 'remarks', 'name'])

        # 生成字典
        user_dict = get_forbidden_users_dict(filter_users_list, user_datas)
        if not user_dict:
            logger.info("失效的CK信息未配置在user_datas内，无需更新")
            return

        # 登录JD获取pt_key
        async with async_playwright() as playwright:
            for user in user_dict:
                logger.info(f"开始更新{user}")
                pt_key = await get_jd_pt_key(playwright, user, mode)
                if pt_key is None:
                    logger.error(f"获取pt_key失败")
                    await send_msg(send_api, send_type=1, msg=f"{user} 更新失败")
                    continue

                req_data = user_dict[user]
                req_data["value"] = f"pt_key={pt_key};pt_pin={user_datas[user]['pt_pin']};"
                logger.info(f"更新内容为{req_data}")
                data = json.dumps(req_data)
                response = await qlapi.set_envs(data=data)
                if response['code'] == 200:
                    logger.info(f"{user}更新成功")
                else:
                    logger.error(f"{user}更新失败, response: {response}")
                    await send_msg(send_api, send_type=1, msg=f"{user} 更新失败")
                    continue

                req_id = f"[{req_data['id']}]" if 'id' in req_data.keys() else f'[\"{req_data["_id"]}\"]'
                data = bytes(req_id, 'utf-8')
                response = await qlapi.envs_enable(data=data)
                if response['code'] == 200:
                    logger.info(f"{user}启用成功")
                    await send_msg(send_api, send_type=0, msg=f"{user} 更新成功")
                else:
                    logger.error(f"{user}启用失败, response: {response}")

    except Exception as e:
        traceback.print_exc()


def parse_args():
    """
    解析参数
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', choices=['cron'], help="运行的main的模式(例如: 'cron')")
    return parser.parse_args()

if __name__ == '__main__':
    # 使用解析参数的函数
    args = parse_args()
    asyncio.run(main(mode=args.mode))
