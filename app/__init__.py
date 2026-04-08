import logging
import os
import sys
import traceback
from pprint import pformat
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from loguru._defaults import LOGURU_FORMAT
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.types import Message

from app.exception.request import AuthException
from app.exception.request import PermissionException
from app.utils.logger import Log
from config import Config

sys.path.append(__file__)

# from starlette_context import middleware, plugins

# 异常类型 hint 映射，用于 AI 自动修复
EXCEPTION_HINTS = {
    "coroutine was never awaited": "异步调用缺少 await，检查是否在 async def 中调用了协程",
    "'NoneType' has no attribute": "对象为 None，检查前置赋值或查询结果是否为空",
    "NoResultFound": "查询结果为空，先用 .scalar_one_or_none() 并判断 None",
    "NoResultFoundError": "查询结果为空，先用 .scalar_one_or_none() 并判断 None",
    "MissingDependencyException": "缺少依赖注入，检查 Depends() 配置是否正确",
    "ValidationError": "请求参数校验失败，检查字段名、类型、必填项",
    "RequestValidationError": "请求参数校验失败，检查请求体 JSON 格式",
    "ConnectionRefusedError": "数据库/Redis 连接被拒绝，确认服务已启动",
    "OperationalError": "数据库操作失败，检查 SQL 语法或连接状态",
    "AttributeError": "属性/方法不存在，检查对象类型或拼写是否正确",
    "TypeError": "类型不匹配，检查参数类型或 None 值传播",
    "pymysql.err": "MySQL 错误，检查 SQL 语法和事务状态",
    "asyncpg": "PostgreSQL 错误，检查 SQL 语法和连接参数",
}


def _get_hint(exc: Exception) -> str:
    """根据异常信息匹配 hint"""
    exc_str = str(exc)
    for key, hint in EXCEPTION_HINTS.items():
        if key in exc_str:
            return hint
    return "查看上方 traceback 确定错误原因"


pity = FastAPI()

# pity.add_middleware(
#     middleware.ContextMiddleware,
#     plugins=(
#         plugins.ForwardedForPlugin(),
#     ),
# )

# 配置日志格式
INFO_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> " \
              "| <level>{level: <8}</level> | <cyan>文件: {extra[filename]}</cyan> " \
              "| 模块: <cyan>{extra[business]}</cyan> | 方法: <cyan>{extra[func]}</cyan> " \
              "| <cyan>行数: {extra[line]}</cyan> | - <level>{message}</level>"

ERROR_FORMAT = "<red>{time:YYYY-MM-DD HH:mm:ss.SSS}</red> " \
               "| <level>{level: <8}</level> | <cyan>文件: {extra[filename]}</cyan> " \
               "| 模块: <cyan>{extra[business]}</cyan> | 方法: <cyan>{extra[func]}</cyan> " \
               "| <cyan>行数: {extra[line]}</cyan> | - <level>{message}</level>"


async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    request._receive = receive


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


@pity.middleware("http")
async def errors_handling(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        hint = _get_hint(exc)
        Log("errors_handling").json_exception(
            error=str(exc),
            hint=hint,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder({
                "code": 110,
                "msg": str(exc),
                "suggestion": hint,
                "path": str(request.url.path),
            })
        )


def error_map(error_type: str, field: str, msg: str = None):
    if "missing" in error_type:
        return f"缺少参数: {field}"
    if "params" in error_type:
        return f"参数: {field} {'不规范' if msg is None else msg}"
    if "not_allowed" in error_type:
        return f"参数: {field} 类型不正确"
    if "type_error" in error_type:
        return f"参数: {field} 类型不合法"
    # Fallback for any unhandled error types
    return f"参数: {field} {msg or error_type}"


@pity.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder({
            "code": 101,
            "msg": error_map(exc.errors()[0]["type"], exc.errors()[0].get("loc", ['unknown'])[-1],
                             exc.errors()[0].get("msg")) if len(exc.errors()) > 0 else "参数解析失败",
        })
    )


@pity.exception_handler(PermissionException)
async def unexpected_exception_error(request: Request, exc: PermissionException):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder({
            "code": 403,
            "msg": exc.detail,
        })
    )


@pity.exception_handler(AuthException)
async def unexpected_exception_error(request: Request, exc: AuthException):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder({
            "code": 401,
            "msg": str(exc.detail),
        })
    )


async def global_execution_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=dict(code=110, msg="unknown error: " + str(exc)),
    )


# add global error
pity.add_middleware(
    ServerErrorMiddleware,
    handler=global_execution_handler,
)
# add cors
pity.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentaion.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def format_record(record: dict) -> str:
    """
    这里的代码是copy的，记录日志格式的
    Custom format for loguru loggers.
    Uses pformat for log any data like request/response body during debug.
    Works with logging if loguru handler it.
    Example:
    # >>> payload = [{"users":[{"name": "Nick", "age": 87, "is_active": True}, {"name": "Alex", "age": 27, "is_active": True}], "count": 2}]
    # >>> logger.bind(payload=).debug("users payload")
    # >>> [   {   'count': 2,
    # >>>         'users': [   {'age': 87, 'is_active': True, 'name': 'Nick'},
    # >>>                      {'age': 27, 'is_active': True, 'name': 'Alex'}]}]
    """

    format_string = str(LOGURU_FORMAT)
    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(
            record["extra"]["payload"], indent=4, compact=True, width=88
        )
        format_string = str(format_string) + "\n<level>{extra[payload]}</level>"

    format_string = str(format_string) + "{exception}\n"
    return format_string


def make_filter(name):
    # 过滤操作，当日志要选择对应的日志文件的时候，通过filter进行筛选
    def filter_(record):
        return record["extra"].get("name") == name

    return filter_


def init_logging():
    loggers = (
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if name.startswith("uvicorn.")
    )
    for uvicorn_logger in loggers:
        uvicorn_logger.handlers = []

    # 这里的操作是为了改变uvicorn默认的logger，使之采用loguru的logger
    # change handler for default uvicorn logger
    intercept_handler = InterceptHandler()
    logging.getLogger("uvicorn").handlers = [intercept_handler]
    # set logs output, level and format
    # logger.add(sys.stdout, level=logging.DEBUG, format=format_record, filter=make_filter('stdout'))
    # 为pity添加一个info log文件，主要记录debug和info级别的日志
    pity_info = os.path.join(Config.LOG_DIR, f"{Config.PITY_INFO}.log")
    # 为pity添加一个error log文件，主要记录warning和error级别的日志
    pity_error = os.path.join(Config.LOG_DIR, f"{Config.PITY_ERROR}.log")
    logger.add(pity_info, enqueue=True, rotation="20 MB", level="DEBUG", filter=make_filter(Config.PITY_INFO))

    logger.add(pity_error, enqueue=True, rotation="10 MB", level="WARNING", filter=make_filter(Config.PITY_ERROR))

    # 配置loguru的日志句柄，sink代表输出的目标
    logger.configure(
        handlers=[
            {"sink": sys.stdout, "level": logging.DEBUG, "format": format_record},
            {"sink": pity_info, "level": logging.INFO, "format": INFO_FORMAT, "filter": make_filter(Config.PITY_INFO)},
            {"sink": pity_error, "level": logging.WARNING, "format": ERROR_FORMAT,
             "filter": make_filter(Config.PITY_ERROR)}
        ]
    )
    return logger
