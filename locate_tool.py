import os
import time
from config import jd_login_url
import pyautogui
from playwright.sync_api import sync_playwright
import random

"""
这个脚本用于滑块的坐标的
"""


def get_position():
    try:
        while True:
            print("Press Ctrl-C to end")
            x, y = pyautogui.position()  # 返回鼠标的坐标
            print(f'slide_x_position, slide_y_position = {x}, {y}')

            time.sleep(0.1)  # 每个1s中打印一次 , 并执行清屏
            os.system('cls')  # 执行系统清屏指令
    except KeyboardInterrupt:
        x, y = pyautogui.position()  # 返回鼠标的坐标
        print(f'slide_x_position, slide_y_position = {x}, {y}')
        return x, y


def main():
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            # 关闭Webdriver属性,绕过Webdriver检测
            js = """Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});"""
            page.add_init_script(js)
            page.goto(jd_login_url)
            page.get_by_text("账号密码登录").click()

            username_input = page.get_by_placeholder("账号名/邮箱/手机号")
            username_input.click()
            username_input.type("1")
            time.sleep(random.random() / 10)

            password_input = page.get_by_placeholder("请输入密码")
            password_input.click()
            password_input.type("1")
            time.sleep(random.random() / 10)

            page.get_by_role("checkbox").check()
            page.get_by_text("登 录").click()

            get_position()

            context.close()
            browser.close()
        except Exception:
            return


if __name__ == '__main__':
    main()
