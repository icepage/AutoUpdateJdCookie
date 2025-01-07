# 项目名
program = "AutoUpdateJdCookie"
# JD登录页
jd_login_url = "https://plogin.m.jd.com/login/login?appid=300&returnurl=https%3A%2F%2Fwq.jd.com%2Fpassport%2FLoginRedirect%3Fstate%3D1103073577433%26returnurl%3Dhttps%253A%252F%252Fhome.m.jd.com%252FmyJd%252Fhome.action&source=wq_passport"
# 支持的形状类型
supported_types = [
    "三角形",
    "正方形",
    "长方形",
    "五角星",
    "六边形",
    "圆形",
    "梯形",
    "圆环"
]
# 定义了支持的每种颜色的 HSV 范围
supported_colors = {
    '紫色': ([125, 50, 50], [145, 255, 255]),
    '灰色': ([0, 0, 50], [180, 50, 255]),
    '粉色': ([160, 50, 50], [180, 255, 255]),
    '蓝色': ([100, 50, 50], [130, 255, 255]),
    '绿色': ([40, 50, 50], [80, 255, 255]),
    '橙色': ([10, 50, 50], [25, 255, 255]),
    '黄色': ([25, 50, 50], [35, 255, 255]),
    '红色': ([0, 50, 50], [10, 255, 255])
}
supported_sms_func = [
    "no",
    "webhook",
    "manual_input"
]
# 默认的UA, 可以在config.py里配置
user_agent = 'Mozilla/5.0 Chrome'