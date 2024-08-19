# linux无GUI使用文档

## 介绍
- 作者认为要用LINUX就用无GUI的，所以未对GUI版本进行测试。
- 主要的卡点在于短信验证码识别，目前支持了，所以可以LINUX上运行。
- 使用手动输入验证码方式进行登录，整体过程如下图

![PNG](./img/linux.png)


## 使用文档
### 安装依赖
```commandline
pip install -r requirements.txt
```

### 安装浏览器驱动
```commandline
playwright install-deps
```

### 安装chromium插件
```commandline
playwright install chromium
```

### 添加配置config.py
- 复制config_example.py, 重命名为config.py, 我们基于这个config.py运行程序;
- user_datas为JD用户数据,按照实际信息填写;
- qinglong_data为QL数据,按照实际信息填写;
  - 建议优先选择用client_id和client_secret,获取方法如下：
  ```commandline
  1、在系统设置 -> 应用设置 -> 添加应用，进行添加
  2、需要【环境变量】的权限
  3、此功能支持青龙2.9+
  ```
  
  - 其次选择用token,需要在浏览器上，F12上获取Authorization的请求头。
  - 账号密码为最次选择, 这种方式会抢占QL后台的登录。

- auto_move为自动识别并移动滑块验证码的开关, 有时不准就关了;
- slide_difference为滑块验证码的偏差, 如果一直滑过了, 或滑不到, 需要调节下;
- auto_shape_recognition为二次图形状验证码的开关;
- headless设置浏览器是否启用无头模式，即是否展示整个登录过程，**必需使用True**
- cron_expression基于cron的表达式，用于schedule_main.py定期进行更新任务
- sms_func为填写验信验证码的模式,有以下三种
  - no 关闭短信验证码识别
  - manual_input 手动在终端输入验证码
  - webhook 调用api获取验证码,可实现全自动填写验证码,暂未实现
- 消息类的配置下面会说明

### 配置消息通知
#### 1、如果不需要发消息，请关掉消息开关，忽略消息配置
```commandline
# 是否开启发消息
is_send_msg = False
```
#### 2、成功消息和失败消息也可以开关
```commandline
# 更新成功后是否发消息的开关
is_send_success_msg = True
# 更新失败后是否发消息的开关
is_send_fail_msg = True
```

#### 3、可以发企微、钉钉、飞书机器人，其它的就自写webhook
```commandline
# 配置发送地址
send_info = {
    "send_wecom": [
        "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key="
    ],
    "send_webhook": [
        "http://127.0.0.1:3000/webhook",
        "http://127.0.0.1:4000/webhook"
    ],
    "send_dingtalk": [
    ],
    "send_feishu": [
    ]
}
```


### 运行脚本
#### 1、单次手动执行
```commandline
python main.py
```

#### 2、常驻进程
进程会读取config.py里的cron_expression,定期进行更新任务
```commandline
python schedule_main.py
```

### 3、定时任务
使用crontab
```commandline
0 3,4 * * * python main.py
```