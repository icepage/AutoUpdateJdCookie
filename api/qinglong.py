from urllib.parse import urljoin
import aiohttp
from enum import Enum
from typing import Union
from utils.tools import send_request

class QlUri(Enum):
    user_login = "api/user/login"
    envs = "api/envs"
    envs_enable = "api/envs/enable"
    envs_disable = "api/envs/disable"


class QlOpenUri(Enum):
    auth_token = "open/auth/token"
    envs = "open/envs"
    envs_enable = "open/envs/enable"
    envs_disable = "open/envs/disable"


class QlApi(object):
    def __init__(self, url: str):
        self.token = None
        self.url = url
        self.headers = None

    def login_by_token(self, token: str):
        headers = {
            'Content-Type': 'application/json'
        }
        self.token = token
        headers['Authorization'] = self.token
        self.headers = headers

    async def login_by_username(self, user: str, password: str):
        data = {
            "username": user,
            "password": password
        }
        headers = {
            'Content-Type': 'application/json'
        }
        response = await send_request(url=urljoin(self.url, QlUri.user_login.value), method="post", headers=headers, data=data)
        if response['code'] == 200:
            self.token = "Bearer " + response["data"]["token"]
            headers['Authorization'] = self.token
            self.headers = headers
        return response

    async def get_envs(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=urljoin(self.url, QlUri.envs.value), headers=self.headers) as response:
                return await response.json()

    async def set_envs(self, data: Union[str, None] = None):
        async with aiohttp.ClientSession() as session:
            async with session.put(url=urljoin(self.url, QlUri.envs.value), data=data, headers=self.headers) as response:
                return await response.json()

    async def envs_enable(self, data: bytes):
        async with aiohttp.ClientSession() as session:
            async with session.put(url=urljoin(self.url, QlUri.envs_enable.value), data=data, headers=self.headers) as response:
                return await response.json()

    async def envs_disable(self, data: bytes):
        async with aiohttp.ClientSession() as session:
            async with session.put(url=urljoin(self.url, QlUri.envs_disable.value), data=data, headers=self.headers) as response:
                return await response.json()


class QlOpenApi(object):
    def __init__(self, url: str):
        self.token = None
        self.url = url
        self.headers = None

    async def login(self, client_id: str, client_secret: str):
        headers = {
            'Content-Type': 'application/json'
        }
        params = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        response = await send_request(url=urljoin(self.url, QlOpenUri.auth_token.value), method="get", headers=headers, params=params)
        if response['code'] == 200:
            self.token = "Bearer " + response["data"]["token"]
            headers['Authorization'] = self.token
            self.headers = headers
        return response

    async def get_envs(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=urljoin(self.url, QlOpenUri.envs.value), headers=self.headers) as response:
                return await response.json()

    async def set_envs(self, data: Union[str, None] = None):
        async with aiohttp.ClientSession() as session:
            async with session.put(url=urljoin(self.url, QlOpenUri.envs.value), data=data, headers=self.headers) as response:
                return await response.json()

    async def envs_enable(self, data: bytes):
        async with aiohttp.ClientSession() as session:
            async with session.put(url=urljoin(self.url, QlOpenUri.envs_enable.value), data=data, headers=self.headers) as response:
                return await response.json()

    async def envs_disable(self, data: bytes):
        async with aiohttp.ClientSession() as session:
            async with session.put(url=urljoin(self.url, QlOpenUri.envs_disable.value), data=data, headers=self.headers) as response:
                return await response.json()
