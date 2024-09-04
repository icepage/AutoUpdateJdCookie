# JD用户信息
user_datas = {
    "13500000000": {
        "password": "123456",
        "pt_pin": "123456",
        "sms_func": "webhook",
        "sms_webhook": "https://127.0.0.1:3000/getCode"
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

# 滑块验证码的偏差, 如果一直滑过了, 或滑不到, 可以调节下
slide_difference = 10

# 是否自动识别移动滑块，有时不准，就关掉吧
auto_move = True

# 是否自动形状验证码识别，有时不准，就关掉吧
auto_shape_recognition = True

# 定时器
cron_expression = "0 5-6 * * *"

# 浏览器是否开启无头模式，即是否展示整个登录过程
headless = False

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
    ]
}

# sms_func为填写验信验证码的模式，有3种可选，webhook待实现
# no 关闭短信验证码识别
# manual_input 手动在终端输入验证码
# TODO: webhook 调用api获取验证码,可实现全自动填写验证码
sms_func = "manual_input"
sms_webhook = "https://127.0.0.1:3000/getCode"