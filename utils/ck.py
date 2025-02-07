import asyncio
from enum import Enum
import json
import random
from utils.tools import send_request
from typing import List, Dict, Any


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
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.42",
        "Accept-Language": "zh-cn",
        "Referer": "https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&",
        "Accept-Encoding": "gzip, deflate, br"
    }
    r = await send_request(url, method, headers)
    # 检测这里太快了, sleep一会儿, 避免FK
    await asyncio.sleep(random.uniform(0.5,2))
    return r


def filter_cks(
    env_data: List[Dict[str, Any]],
    *,
    status: int = None,
    id: int = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    过滤env_data中符合条件的字典。

    :param env_data: ql环境变量数据
    :param status: 过滤条件之一，status字段的值。
    :param id: 过滤条件之一，id字段的值。
    :param kwargs: 其他过滤条件。
    :return: 符合条件的字典列表。
    """
    # 检查必传参数是否至少传了一个
    if status is None and id is None and not kwargs:
        raise ValueError("至少需要传入一个过滤条件（status、id或其他字段）。")

    # 合并所有过滤条件
    filters = {}
    if status is not None:
        filters["status"] = status
    if id is not None:
        filters["id"] = id
    # 添加其他过滤条件
    filters.update(kwargs)

    # 过滤数据
    filtered_list = []

    for item in env_data:
        if all(item.get(key) == value for key, value in filters.items()):
            filtered_list.append(item)

    return filtered_list


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
    # 过滤出启用的CK
    jd_ck_list = filter_cks(env_data, status=0, name='JD_COOKIE')

    # 检测CK是否失效
    invalid_cks_list = await get_invalid_cks(jd_ck_list)

    data = bytes(json.dumps([ck['id'] if 'id' in ck.keys() else ck["_id"] for ck in invalid_cks_list]), 'utf-8')
    return data
