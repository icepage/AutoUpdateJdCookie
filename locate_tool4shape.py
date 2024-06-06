import asyncio
from pynput import mouse
from config import jd_login_url
from main import auto_move_slide
from playwright.async_api import async_playwright
import random

"""
这个脚本用于形状码的坐标的
"""


def get_position(x_name, y_name, detail):
    print(f"请点击{detail},将获取坐标 ...")

    def on_click(x, y, button, pressed):
        if pressed:
            print(f"{x_name}, {y_name} = {x}, {y}")
            return False  # 停止监听事件

    with mouse.Listener(on_click=on_click) as listener:
        listener.join()


async def main():
    async with async_playwright() as playwright:
        try:
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
            await username_input.type("1")
            await asyncio.sleep(random.random() / 10)

            password_input = page.get_by_placeholder("请输入密码")
            await password_input.click()
            await password_input.type('1')

            await page.get_by_role("checkbox").check()
            await page.get_by_text("登 录").click()

            await auto_move_slide(page, retry_times=5)

            await asyncio.sleep(random.random() / 10)
            get_position("backend_top_left_x", "backend_top_left_y", "形状图的左上角")

            await context.close()
            await browser.close()
        except Exception:
            return


if __name__ == '__main__':
    asyncio.run(main())
