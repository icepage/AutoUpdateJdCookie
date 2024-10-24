# linux无GUI使用文档

## 介绍
- 作者认为要用LINUX就用无GUI的，所以未对GUI版本进行测试。
- 主要的卡点在于短信验证码识别，目前支持了，所以可以LINUX上运行。
- 使用手动输入验证码方式进行登录，整体过程如下图
- 支持docker部署
- 支持的账号类型有：
  - 账号密码登录
  - QQ登录
- 支持代理
![PNG](./img/linux.png)


## 使用文档
## 1、docker部署(推荐)

### 下载镜像
```shell
docker pull icepage/aujc:latest
```

### 配置config.py
- 下载本项目的config_example.py, 重命名为config.py; 
- 配置config.py, 配置文件说明请转向 [配置文件说明](https://github.com/icepage/AutoUpdateJdCookie/blob/main/配置文件说明.md)
- config.py的**cron_expression**参数必填;
- config.py的**headless一定要设为True!!!!**

### 手动执行
- 2种场景下需要手动main.py
  - 1、需要短信验证时需要手动, 本应用在新设备首次更新时必现. 
  - 2、定时时间外需要执行脚本. 
- 配置中的sms_func设为manual_input时, 才能在终端填入短信验证码。
- 当需要手动输入验证码时, docker运行需加-i参数。否则在触发短信验证码时会报错Operation not permitted
```bash
docker run -i -v $PWD/config.py:/app/config.py icepage/aujc:latest python main.py
```

![PNG](./img/linux.png)

### 长期运行
- 程序读config.py中的cron_expression, 定期进行更新任务
- PS：当sms_func设置为manual_input, 在长期运行时是不适用的，因为没地方可填验证码. 
```bash
docker run -v $PWD/config.py:/app/config.py icepage/aujc:latest
```

## 2、本地部署
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
- 配置config.py, 配置文件说明请转向 [配置文件说明](https://github.com/icepage/AutoUpdateJdCookie/blob/main/配置文件说明.md)

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