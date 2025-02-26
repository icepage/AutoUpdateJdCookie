import aiohttp
import base64
import hashlib
import hmac
import time
from typing import Dict, Any
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
    async def send_pushplus(url: str, msg: str) -> Dict[str, Any]:
        """
        发送 Pushplus 消息。

        Args:
            url (str): Pushplus 的消息接收 URL: http://www.pushplus.plus/send?token=xxxxxxxxx。
            msg (str): 要发送的消息内容。

        Returns:
            Dict[str, Any]: 返回发送消息的结果。
        """
        data = {
            "content": msg
        }
        return await send_message(url, data)
