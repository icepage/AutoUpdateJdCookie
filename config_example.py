# JD用户信息
user_datas = {
    "13500000000": {
        "password": "123456",
        "pt_pin": "123456",
        "sms_func": "webhook",
        "sms_webhook": "https://127.0.0.1:3000/getCode",
        # 设置为True时, 即使账号未失效也更新
        "force_update": False
    },
    # QQ账号
    "168465451": {
        # qq密码
        "password": "123456",
        "pt_pin": "123456",
        # 指定为qq账号
        "user_type": "qq",
        "force_update": True
    },
    "13500000001": {
        "password": "123456",
        "pt_pin": "123456",
        "sms_func": "no"
    },
    "13500000002": {
        "password": "123456",
        "pt_pin": "123456",
    },
}

# ql信息
qinglong_data = {
    "url": "http://127.0.0.1:5700/",
    "client_id": "",
    "client_secret": "",
    "username": "admin",
    "password": "123456",
    # 可选参数，QL面板的sessionid，主要是避免抢占QL后台的登录。需要在浏览器上，F12上获取Authorization的请求头。如果为空或不设置则账号密码登录
    "token": ""
}

# 定时器
cron_expression = "0 5-6 * * *"

# 浏览器是否开启无头模式，即是否展示整个登录过程
headless = True

# 是否开启发消息
is_send_msg = False
# 更新成功后是否发消息的开关
is_send_success_msg = True
# 更新失败后是否发消息的开关
is_send_fail_msg = True
# 配置发送地址
send_info = {
    "send_wecom": [
    ],
    "send_webhook": [
    ],
    "send_dingtalk": [
    ],
    "send_feishu": [
    ],
    "send_pushplus": [
    ]
}

# sms_func为填写验信验证码的模式，有3种可选，如下：
# no 关闭短信验证码识别
# manual_input 手动在终端输入验证码
# webhook 调用api获取验证码,可实现全自动填写验证码
sms_func = "manual_input"
sms_webhook = "https://127.0.0.1:3000/getCode"

# voice_func为手机语音验证码的模式，no为关闭识别，manual_input为手动在终端输入验证码
voice_func = "manual_input"

# 代理的配置，只代理登录，不代理请求QL面板和发消息
proxy = {
    # 代理服务器地址, 支持http, https, socks5
    "server": "http://",
    # 代理服务器账号
    "username": "",
    # 代理服务器密码
    "password": ""
}