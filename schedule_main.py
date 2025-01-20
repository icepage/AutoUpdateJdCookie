import asyncio
from datetime import datetime, timedelta
from croniter import croniter
from importlib import reload
from utils.consts import program
import config
from main import main
from loguru import logger


def get_next_runtime(cron_expression, base_time=None):
    base_time = base_time or datetime.now()
    cron = croniter(cron_expression, base_time)
    return cron.get_next(datetime)


async def run_scheduled_tasks():
    logger.info(f"{program}运行中")
    next_run = get_next_runtime(config.cron_expression)
    logger.info(f"下次更新任务时间为{next_run}")
    while True:
        now = datetime.now()
        if now >= next_run:
            reload(config)  # 重新加载配置文件
            await main(mode="cron")
            next_run = get_next_runtime(config.cron_expression, now + timedelta(seconds=1))
            logger.info(f"下次更新任务时间为{next_run}")
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_scheduled_tasks())
