import time
from functools import wraps
from app.config.settings import logger

def async_timing(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f".:.{func.__name__}.:. executed in {duration:.2f}s")
        return result
    return wrapper