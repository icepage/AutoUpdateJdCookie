# JD用户信息
user_datas = {
    "13500000000": {
        "password": "123456",
        "pt_pin": "123456"
    },
    "13500000001": {
        "password": "123456",
        "pt_pin": "123456"
    },
}
# JD登录页
jd_login_url = "https://plogin.m.jd.com/login/login?appid=300&returnurl=https%3A%2F%2Fwq.jd.com%2Fpassport%2FLoginRedirect%3Fstate%3D1103073577433%26returnurl%3Dhttps%253A%252F%252Fhome.m.jd.com%252FmyJd%252Fhome.action&source=wq_passport"

# ql信息
qinglong_data = {
    "url": "http://127.0.0.1:5700/",
    "username": "admin",
    "password": "123456",
    # 可选参数，QL面板的sessionid，主要是避免抢占QL后台的登录。需要在浏览器上，F12上获取Authorization的请求头。如果为空或不设置则账号密码登录
    "token": ""
}
# 滑块距离屏幕左上角的x, y像素, 需根据自己屏幕大小调整
slide_x_position, slide_y_position = 533, 572

# 滑块验证码的偏差, 如果一直滑过了, 或滑不到, 可以调节下
slide_difference = 10

# 是否自动识别移动滑块，有时不准，就关掉吧
auto_move = True

# 是否自动形状验证码识别，有时不准，就关掉吧
auto_shape_recognition = True

# 形状图的左上角坐标
backend_top_left_x, backend_top_left_y = 505, 340

# 截取文字区域的左上和右下坐标
# 左上角坐标
small_img_top_left_x, small_img_top_left_y = 500, 534
# 右下角坐标
small_img_bottom_right_x, small_img_bottom_right_y = 800, 559
