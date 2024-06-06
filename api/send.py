import aiohttp
from typing import Dict, Any


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
