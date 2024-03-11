# MyJdCOOKIE

### 介绍
- 用来自动化更新青龙面板的失效JD_COOKIE, 主要有三步
    - 自动化获取青龙面板的失效JD_COOKIE
    - 基于失效JD_COOKIE, 自动化登录JD,包括滑块验证, 拿到key
    - 基于key, 自动化更新青龙面板的失效JD_COOKIE
- python >= 3.9 (playwright依赖的typing，在3.7和3.8会报错typing.NoReturn的BUG)
- 基于windows
- 整体效果如下图

![GIF](./img/main.gif)

### TODOLIST
- 批量更新多账号(已实现)
- selenium加载太慢，用playwright改写(已实现)
- 自动识别拖动验证码(已实现，but成功率为90%，且偶尔会被JD识别)
- 加日志(已实现)
- 写使用文档(已实现)
- 加一些通知如钉钉等
- 添加获取滑块x,y坐标的工具(已实现)

## 使用文档
### 安装依赖
```commandline
pip install -r requirements.txt
```

### 安装chromium插件
```commandline
playwright install chromium
```

### 获取滑块的坐标
```commandline
python locate_tool.py
```
运行脚本后，将鼠标放置到滑块处，按下ctrl+c退出，打到终端打印的坐标，参考下图

![GIF](./img/get_location.gif)

### 添加配置
- 复制config_example.py, 重命名为config.py, 我们基于这个config.py运行程序;
- slide_x_position, slide_y_position用locate_tool.py拿到;
- auto_move为自动识别并移动滑块验证码的开关, 有时不准就关了;
- slide_difference为滑块验证码的偏差, 如果一直滑过了, 或滑不到, 需要调节下;
- 有时多次失败，滑块验证码会变成其它验证码，或需要收到短信验证码，需要手动处理;
- 其它配置按实际填写.

### 运行脚本
```commandline
python main.py
```