import os


def prompt_input(prompt, default=None, required=False, choices=None):
    while True:
        suffix = f" (默认: {default})" if default is not None else ""
        user_input = input(f"{prompt}{suffix}: ").strip()
        if not user_input and default is not None:
            return default
        if choices and user_input not in choices:
            print(f"⚠️  请输入以下选项之一: {', '.join(choices)}")
            continue
        if user_input or not required:
            return user_input
        print("⚠️  此项为必填，请重新输入。")


def prompt_yes_no(prompt, default='y'):
    choices_show = 'Y/n' if default.lower() == 'y' else 'y/N'
    while True:
        choice = input(f"{prompt} ({choices_show}): ").strip().lower()
        if not choice:
            return default.lower() == 'y'
        if choice in ['y', 'n']:
            return choice == 'y'
        print("⚠️  请输入 'y' 或 'n'。")


def collect_user_datas():
    print("\n================= 配置账号信息 =================")
    user_datas = {}
    index = 1
    while True:
        print(f"\n第 {index} 个账号配置:")
        username = prompt_input("用户名 (留空则结束输入)")
        if not username:
            if index == 1:
                print("⚠️  至少需要配置一个账号！")
                continue
            break
        user_type = prompt_input("账号类型 (jd/qq)", default="jd", choices=["jd", "qq"])
        password = prompt_input("密码", required=True)
        pt_pin = prompt_input("pt_pin (必填)", required=True)
        force_update = prompt_yes_no("是否强制更新？(默认为n)", default='n')
        auto_switch = prompt_yes_no("是否自动处理验证码？(默认为y)", default='y')
        individual_sms = prompt_yes_no("是否单独配置短信验证码处理方式？(默认为n)", default='n')
        sms_func = None
        sms_webhook = None
        if individual_sms:
            sms_func = prompt_input("短信验证码处理方式 (no/manual_input/webhook) (默认为manual_input)", default="manual_input",
                                    choices=["no", "manual_input", "webhook"])
            if sms_func == "webhook":
                sms_webhook = prompt_input("请输入短信验证码 webhook 地址", required=True)

        user_data = {
                "user_type": user_type,
                "password": password,
                "pt_pin": pt_pin,
                "force_update": force_update,
                "auto_switch": auto_switch
        }
        if individual_sms:
            user_data["sms_func"] = sms_func
            if sms_webhook:
                user_data["sms_webhook"] = sms_webhook

        user_datas[username] = user_data
        index += 1
    return user_datas


def collect_qinglong_data():
    print("\n================= 配置青龙面板 =================")
    url = prompt_input("青龙面板 URL (如 http://127.0.0.1:5700)", required=True)
    while True:
        client_id = prompt_input("client_id (可选)")
        client_secret = prompt_input("client_secret (可选)")
        token = prompt_input("token (可选)")
        username = prompt_input("青龙用户名 (可选)")
        password = prompt_input("青龙密码 (可选)")
        if (client_id and client_secret) or token or (username and password):
            break
        print("⚠️  必须填写以下认证方式之一：client_id+client_secret、token、用户名+密码")
    qinglong_data = {
        "url": url,
        "client_id": client_id if client_id else "",
        "client_secret": client_secret if client_secret else "",
        "token": token if token else "",
        "username": username if username else "",
        "password": password if password else ""
     }

    return qinglong_data


def collect_send_info():
    print("\n================= 配置消息通知 =================")

    def collect_urls(name, display_name):
        urls = []
        print(f"请输入 {display_name} 的通知地址（支持多个，输入为空结束）：")
        while True:
            url = input(f"{display_name} 通知地址: ").strip()
            if not url:
                break
            urls.append(url)
        return urls if urls else None

    send_info = {}

    services = [
        ("send_wecom", "企业微信"),
        ("send_webhook", "自定义 Webhook"),
        ("send_dingtalk", "钉钉"),
        ("send_feishu", "飞书"),
        ("send_pushplus", "PushPlus"),
    ]

    for key, display in services:
        urls = collect_urls(key, display)
        if urls:
            send_info[key] = urls

    return send_info



def collect_proxy():
    print("\n================= 配置代理 =================")
    server = prompt_input("代理服务器地址 (如 http://127.0.0.1:7890，留空则不使用代理)")
    if not server:
        return None
    username = prompt_input("代理服务器用户名 (可选)")
    password = prompt_input("代理服务器密码 (可选)")
    proxy = {
        "server": server
    }
    if username:
        proxy["username"] = username
    if password:
        proxy["password"] = password
    return proxy


def write_config(user_datas, qinglong_data, headless, cron_expression, is_send_msg, is_send_success_msg,
                 is_send_fail_msg, send_info, sms_func, voice_func, proxy, user_agent, enable_desensitize):
    if os.path.exists("config.py"):
        print("\n------------------- 文件存在 -------------------")
        overwrite = prompt_yes_no("检测到已有 config.py，是否覆盖？", default='n')
        if not overwrite:
            print("⚠️  已取消生成 config.py")
            return

    with open("config.py", "w", encoding="utf-8") as f:
        f.write("user_datas = {\n")
        for uid, user in user_datas.items():
            f.write(f"    '{uid}': {{\n")
            for key, value in user.items():
                if isinstance(value, bool):
                    f.write(f"        '{key}': {value},\n")
                else:
                    f.write(f"        '{key}': '{value}',\n")
            f.write("    },\n")
        f.write("}\n\n")

        f.write("qinglong_data = {\n")
        for key, value in qinglong_data.items():
            f.write(f"    '{key}': '{value}',\n")
        f.write("}\n\n")

        f.write(f"headless = {headless}\n")
        f.write(f"cron_expression = '{cron_expression}'\n")
        f.write(f"is_send_msg = {is_send_msg}\n")
        f.write(f"is_send_success_msg = {is_send_success_msg}\n")
        f.write(f"is_send_fail_msg = {is_send_fail_msg}\n")

        if send_info:
            f.write("send_info = {\n")
            for key, value in send_info.items():
                f.write(f"    '{key}': {value},\n")
            f.write("}\n")

        f.write(f"sms_func = '{sms_func}'\n")
        f.write(f"voice_func = '{voice_func}'\n")

        if proxy:
            f.write("proxy = {\n")
            for key, value in proxy.items():
                f.write(f"    '{key}': '{value}',\n")
            f.write("}\n")

        if user_agent:
            f.write(f"user_agent = '{user_agent}'\n")

        f.write(f"enable_desensitize = {enable_desensitize}\n")

    print("\n✅ 成功生成 config.py！")


def main():
    print("============== 欢迎使用 AutoUpdateJdCookie 配置生成器 ==============")

    user_datas = collect_user_datas()
    qinglong_data = collect_qinglong_data()

    print("\n================= 配置全局参数 =================")
    headless = prompt_yes_no("是否启用无头模式？(默认启用)", default='y')
    cron_expression = prompt_input("定时任务 Cron 表达式", default="15 0 * * *", required=True)

    print("\n================= 配置消息通知 =================")
    is_send_msg = prompt_yes_no("是否启用消息通知？(默认为n)", default='n')
    is_send_success_msg = False
    is_send_fail_msg = False
    send_info = {}
    if is_send_msg:
        is_send_success_msg = prompt_yes_no("更新成功后通知？", default='y')
        is_send_fail_msg = prompt_yes_no("更新失败后通知？", default='y')
        send_info = collect_send_info()

    print("\n================= 配置短信验证码方式 =================")
    sms_func = prompt_input("全局短信验证码处理方式 (no/manual_input/webhook)", default="manual_input", choices=["no", "manual_input", "webhook"])

    print("\n================= 其它配置 =================")
    voice_func = prompt_input("语音验证码处理方式 (no/manual_input)", default="no", choices=["no", "manual_input"])
    proxy = collect_proxy()
    user_agent = prompt_input("User-Agent (留空使用默认)")
    enable_desensitize = prompt_yes_no("是否启用日志和发送消息脱敏？(默认不开启)", default='n')

    write_config(
        user_datas, qinglong_data, headless, cron_expression,
        is_send_msg, is_send_success_msg, is_send_fail_msg,
        send_info, sms_func, voice_func, proxy, user_agent, enable_desensitize
    )



if __name__ == "__main__":
    main()
