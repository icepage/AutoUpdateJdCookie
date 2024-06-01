import asyncio
from api.qinglong import QlApi
from config import (
    slide_difference,
    slide_x_position,
    slide_y_position,
    auto_move,
    qinglong_data,
    user_datas,
    jd_login_url,
    auto_shape_recognition,
    backend_top_left_x,
    backend_top_left_y,
    small_img_top_left_x,
    small_img_top_left_y,
    small_img_bottom_right_x,
    small_img_bottom_right_y
)
from loguru import logger
import time
from playwright.async_api import Playwright, async_playwright
import random
import traceback
from typing import Union
from utils.consts import supported_types
from utils.tools import (
    base_move,
    get_img_bytes,
    get_forbidden_users_dict,
    filter_forbidden_users,
    save_img,
    get_ocr,
    get_word,
    save_screenshot_img,
    get_shape_location_by_type,
    click_by_autogui
)

"""
基于playwright做的
"""
logger.add("main.log", format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}", level="DEBUG")


async def auto_move_slide(page, retry_times: int=2):
    """
    自动识别移动滑块验证码
    """
    for i in range(retry_times):
        logger.info(f'第{i}次尝试自动移动滑块中...')
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

        # 识别移动滑块
        base_move(slide_x_position, slide_y_position, small_img_bytes, background_img_bytes, slide_difference)
        time.sleep(3)


async def auto_shape(page, retry_times: int=5):
    ocr = get_ocr(beta=True)
    """
    自动识别滑块验证码
    """
    for i in range(retry_times):
        logger.info(f'第{i}次自动识别形状中...')
        try:
            # 查找小图
            await page.wait_for_selector('#cpc_img', state='visible', timeout=3000)
        except Exception as e:
            # 未找到元素，认为成功，退出循环
            logger.info('未找到形状图,退出识别状态')
            break
        # 获取 图片的src 属性和button按键
        background_src = await page.locator('#cpc_img').get_attribute('src')
        button = page.locator('div.captcha_footer button.sure_btn')

        # 找到刷新按钮
        refresh_button = page.locator('div.captcha_header img.jcap_refresh')

        # 截文字小图,返回小图path
        small_img_path = save_screenshot_img(small_img_top_left_x, small_img_top_left_y, small_img_bottom_right_x, small_img_bottom_right_y, 'small_img')

        # 获取大图并保存
        background_img_bytes = get_img_bytes(background_src)
        background_img_path = save_img('background_img', background_img_bytes)

        # 获取问题的文字
        word = get_word(ocr, small_img_path)

        if word.find('色') > 0:
            logger.info(f'不支持颜色,刷新中......')
            # 刷新
            await refresh_button.click()
            await asyncio.sleep(random.random() * 2)
            continue
        else:
            type = word.split('请选出图中的')[1]
            if type in supported_types:
                logger.info(f'已找到图形,点击中......')
                # 获取点的中心点
                center_x, center_y = get_shape_location_by_type(background_img_path, type)
                if center_x is None and center_y is None:
                    logger.info(f'识别失败,刷新中......')
                    await refresh_button.click()
                    continue
                # 得到网页上的中心点
                x, y = backend_top_left_x + center_x ,backend_top_left_y + center_y
                # 点击图片
                click_by_autogui(x, y)
                await asyncio.sleep(random.random() * 3)
                # 点击确定
                await button.click()
                await asyncio.sleep(3)
                continue
            else:
                logger.info(f'不支持该类型形状,刷新中......')
                # 刷新
                await refresh_button.click()
                await asyncio.sleep(random.random() * 3)
                continue


async def get_jd_pt_key(playwright: Playwright, user) -> Union[dict, None]:
    """
    获取jd的pt_key
    """
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    # 关闭Webdriver属性,绕过Webdriver检测
    js = """Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});"""
    await page.add_init_script(js)
    await page.goto(jd_login_url)
    await page.get_by_text("账号密码登录").click()

    username_input = page.get_by_placeholder("账号名/邮箱/手机号")
    await username_input.click()
    for u in user:
        await username_input.type(u, no_wait_after=True)
        await asyncio.sleep(random.random() / 10)

    password_input = page.get_by_placeholder("请输入密码")
    await password_input.click()
    password = user_datas[user]["password"]
    for p in password:
        await password_input.type(p, no_wait_after=True)
        await asyncio.sleep(random.random() / 10)

    await page.get_by_role("checkbox").check()
    await page.get_by_text("登 录").click()

    # 自动识别移动滑块验证码
    if auto_move:
        # 关键的sleep
        time.sleep(2)
        await auto_move_slide(page, retry_times=5)

    # 自动验证形状验证码
    if auto_shape_recognition:
        time.sleep(2)
        await auto_shape(page, retry_times=30)

    # 等待滑块验证码通过
    await page.wait_for_selector('#msShortcutMenu', state='visible', timeout=120000)

    cookies = await context.cookies()
    for cookie in cookies:
        if cookie['name'] == 'pt_key':
            pt_key = cookie["value"]
            break

    await context.close()
    await browser.close()
    return pt_key


async def main():
    try:
        qlapi = QlApi(qinglong_data["url"], qinglong_data.get("username"), qinglong_data.get("password"), qinglong_data.get('token'))
        # 拿到禁用的用户列表
        env = await qlapi.get_envs()
        user_info = env['data']
        # 获取禁用用户
        forbidden_users = [x for x in user_info if x['name'] == 'JD_COOKIE' and x['status'] == 1]
        # logger.info(f"forbidden_users: {forbidden_users}")
        if not forbidden_users:
            logger.info("All users are functioning normally")
            return

        # 获取需要的字段
        filter_users_list = filter_forbidden_users(forbidden_users, ['id', 'value', 'remarks', 'name'])

        # 生成字典
        user_dict = get_forbidden_users_dict(filter_users_list, user_datas)
        # logger.info(f"user_dict: {user_dict}")

        # 登录JD获取pt_key
        async with async_playwright() as playwright:
            # 获取token_list, 获取一个{"13500000000": pt_key1, "13500000001": pt_key2}的dict
            token_dict = {}
            for user in user_dict:
                pt_key = await get_jd_pt_key(playwright, user)
                token_dict[user] = pt_key
        # logger.info(f"token_dict: {token_dict}")

        # 更新JD_COOKIE
        for user in user_dict:
            user_info = user_dict[user]
            user_info["value"] = f"pt_key={token_dict[user]};pt_pin={user_datas[user]['pt_pin']};"
            response = await qlapi.set_envs(data=user_info)
            if response['code'] == 200:
                logger.info(f"{user} update sucess")
            else:
                logger.error(f"{user} update fail")

            data = bytes(f"[{user_info['id']}]", 'utf-8')
            response = await qlapi.envs_enable(data=data)
            if response['code'] == 200:
                logger.info(f"{user} envs_enable sucess")
            else:
                logger.error(f"{user} envs_enable fail")

    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
