import aiohttp
import base64
import hashlib
import hmac
import time
from typing import Dict, Any
import asyncio
import json
import urllib

def generate_sign(secret):
    """
    钉钉加签
    """
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign

async def send_message(url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    发消息的通用方法
    """
    headers = {
        'Content-Type': 'application/json',
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json()

class WeCom:
    def __init__(self, corpid, corpsecret, agentid):
        self.CORPID = corpid
        self.CORPSECRET = corpsecret
        self.AGENTID = agentid

    async def get_access_token(self):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        params = {'corpid': self.CORPID, 'corpsecret': self.CORPSECRET}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                return data.get("access_token")  # 使用 get 方法避免 KeyError

    async def send_text(self, message, touser="@all"):
        access_token = await self.get_access_token()
        send_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        send_values = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.AGENTID,
            "text": {
                "content": message
            },
            "safe": "0"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(send_url, json=send_values) as response:
                response_data = await response.json()
                return response_data.get("errmsg", "未知错误")  # 使用 get 方法避免 KeyError

    async def send_mpnews(self, title, message, media_id, touser="@all"):
        access_token = await self.get_access_token()
        send_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        send_values = {
            "touser": touser,
            "msgtype": "mpnews",
            "agentid": self.AGENTID,
            "mpnews": {
                "articles": [
                    {
                        "title": title,
                        "thumb_media_id": media_id,
                        "author": "Author",
                        "content_source_url": "",
                        "content": message.replace('\n', '<br/>'),
                        "digest": message
                    }
                ]
            }
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(send_url, json=send_values) as response:
                response_data = await response.json()
                return response_data.get("errmsg", "未知错误")  # 使用 get 方法避免 KeyError

class SendApi(object):
    def __init__(self, name):
        self.name = name

    @staticmethod
    async def send_webhook(url, msg):
        """
        webhook
        """
        data = {
            "content": msg
        }
        return await send_message(url, data)

    @staticmethod
    async def send_wecom(url, msg):
        """
        企业微信
        """
        data = {
            "msgtype": "text",
            "text": {
                "content": msg
            }
        }
        return await send_message(url, data)

    @staticmethod
    async def send_dingtalk(url: str, msg: str) -> Dict[str, Any]:
        """
        钉钉
        """
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        # 必须有access_token
        access_token = query_params["access_token"][0]
        secret = query_params.get("secret", [None])[0]
        url = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"

        if secret:
            timestamp, sign = generate_sign(secret)
            url = f"{url}&timestamp={timestamp}&sign={sign}"
        data = {
            "msgtype": "text",
            "text": {
                "content": msg
            }
        }
        return await send_message(url, data)

    @staticmethod
    async def send_feishu(url: str, msg: str) -> Dict[str, Any]:
        """
        飞书
        """
        data = {
            "msg_type": "text",
            "content": {
                "text": msg
            }
        }
        return await send_message(url, data)

    @staticmethod
    async def send_wecom_app(url: str, msg: str) -> Dict[str, Any]:
        """
        企业微信应用发送消息
        """
        params = url.split(",")
        corpid = params[0]
        corpsecret = params[1]
        touser = params[2]
        agentid = params[3]

        try:
            mediaid = params[4]
        except IndexError:
            mediaid = None  # 用 None 表示没有 media_id

        wx = WeCom(corpid, corpsecret, agentid)

        # 检查是否存在 mediaid，如果存在则发送图文消息，反之发送文本消息
        if mediaid:
            response = await wx.send_mpnews("京东账号自动更新报告", msg, mediaid, touser)
        else:
            response = await wx.send_text(msg, touser)

        return {"status": response}
