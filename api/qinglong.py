import aiohttp
from loguru import logger
import requests
import json
from enum import Enum
logger.add("main.log", format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}", level="DEBUG")


class QlUri(Enum):
    user_login = "api/user/login"
    envs = "api/envs"


class QlApi(object):
    def __init__(self, url: str, user: str, password: str):
        self.url = url
        self.user = user
        self.password = password
        self.token = "Bearer " + self.login()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': self.token
        }

    def login(self):
        data = {
            "username": self.user,
            "password": self.password
        }
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(url=f"{self.url}/{QlUri.user_login.value}", data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            token = json.loads(response.text)["data"]["token"]
            logger.info("Login successful. Token obtained.")
            return token
        else:
            logger.error(f"Login failed. Status code: {response.status_code}")

    async def get_envs(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.url}/{QlUri.envs.value}", headers=self.headers) as response:
                if response.status == 200:
                    logger.info("Get Envs successful. Token obtained.")
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Get Envs failed. Status code: {response.status}")

    async def set_envs(self, data: dict = None):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.url}/{QlUri.envs.value}", data=json.dumps(data), headers=self.headers) as response:
                if response.status == 200:
                    logger.info("Set Envs successful. Token obtained.")
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Set Envs failed. Status code: {response.status}")
