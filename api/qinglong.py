import aiohttp
import requests
import json
from enum import Enum
from typing import Union


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

    def login_by_username(self, user: str, password: str):
        data = {
            "username": user,
            "password": password
        }
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(url=f"{self.url}/{QlUri.user_login.value}", data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            self.token = "Bearer " + response.json()["data"]["token"]
            headers['Authorization'] = self.token
            self.headers = headers
        return response

    async def get_envs(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.url}/{QlUri.envs.value}", headers=self.headers) as response:
                return await response.json()

    async def set_envs(self, data: Union[str, None] = None):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.url}/{QlUri.envs.value}", data=data, headers=self.headers) as response:
                return await response.json()

    async def envs_enable(self, data: bytes):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.url}/{QlUri.envs_enable.value}", data=data, headers=self.headers) as response:
                return await response.json()

    async def envs_disable(self, data: bytes):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.url}/{QlUri.envs_disable.value}", data=data, headers=self.headers) as response:
                return await response.json()


class QlOpenApi(object):
    def __init__(self, url: str):
        self.token = None
        self.url = url
        self.headers = None

    def login(self, client_id: str, client_secret: str):
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.get(url=f"{self.url}/{QlOpenUri.auth_token.value}?client_id={client_id}&client_secret={client_secret}", headers=headers)
        if response.status_code == 200:
            self.token = "Bearer " + response.json()["data"]["token"]
            headers['Authorization'] = self.token
            self.headers = headers
        return response

    async def get_envs(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.url}/{QlOpenUri.envs.value}", headers=self.headers) as response:
                return await response.json()

    async def set_envs(self, data: Union[str, None] = None):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.url}/{QlOpenUri.envs.value}", data=data, headers=self.headers) as response:
                return await response.json()

    async def envs_enable(self, data: bytes):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.url}/{QlOpenUri.envs_enable.value}", data=data, headers=self.headers) as response:
                return await response.json()

    async def envs_disable(self, data: bytes):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.url}/{QlOpenUri.envs_disable.value}", data=data, headers=self.headers) as response:
                return await response.json()
