import asyncio
from enum import Enum
import random
from utils.tools import send_request, sanitize_header_value
from typing import List, Any


class CheckCkCode(Enum):
    not_login = 1001


async def check_ck(
        cookie: str
) -> dict[str, Any]:
    """
    检测JD_COOKIE是否失效

    :param cookie: 就是cookie
    """
    url = "https://me-api.jd.com/user_new/info/GetJDUserInfoUnion"
    method = 'get'
    headers = {
        "Host": "me-api.jd.com",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Cookie": sanitize_header_value(cookie),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.42",
        "Accept-Language": "zh-cn",
        "Referer": "https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&",
        "Accept-Encoding": "gzip, deflate, br"
    }
    r = await send_request(url, method, headers)
    # 检测这里太快了, sleep一会儿, 避免FK
    await asyncio.sleep(random.uniform(0.5,2))
    return r


async def get_invalid_cks(
    jd_ck_list: list
) -> List[dict]:
    """
    传入CK列表，过滤失效CK列表
    """
    ck_list = []
    for jd_ck in jd_ck_list:
        cookie = jd_ck['value']
        r = await check_ck(cookie)
        if r.get('retcode') == str(CheckCkCode.not_login.value):
            ck_list.append(jd_ck)

    return ck_list


async def get_invalid_ck_ids(env_data):
    # 检测CK是否失效
    invalid_cks_list = await get_invalid_cks(env_data)

    invalid_cks_id_list = [ck['id'] if 'id' in ck.keys() else ck["_id"] for ck in invalid_cks_list]
    return invalid_cks_id_list
