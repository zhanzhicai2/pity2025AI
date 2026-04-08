import inspect
import json
import os
import traceback as tb
from datetime import datetime

from loguru import logger

from config import Config


# @SingletonDecorator
class Log(object):
    business = None

    def __init__(self, name='pity'):  # Logger标识默认为app
        """
        :param name: 业务名称
        """
        # 如果目录不存在则创建
        if not os.path.exists(Config.LOG_DIR):
            os.mkdir(Config.LOG_DIR)
        self.business = name

    def info(self, message: str):
        file_name, line, func, _, _ = inspect.getframeinfo(inspect.currentframe().f_back)
        logger.bind(name=Config.PITY_INFO, func=func, line=line,
                    business=self.business, filename=file_name).debug(message)

    def error(self, message: str):
        file_name, line, func, _, _ = inspect.getframeinfo(inspect.currentframe().f_back)
        logger.bind(name=Config.PITY_ERROR, func=func, line=line,
                    business=self.business, filename=file_name).error(message)

    def warning(self, message: str):
        file_name, line, func, _, _ = inspect.getframeinfo(inspect.currentframe().f_back)
        logger.bind(name=Config.PITY_ERROR, func=func, line=line,
                    business=self.business, filename=file_name).warning(message)

    def debug(self, message: str):
        file_name, line, func, _, _ = inspect.getframeinfo(inspect.currentframe().f_back)
        logger.bind(name=Config.PITY_INFO, func=func, line=line,
                    business=self.business, filename=file_name).debug(message)

    def exception(self, message: str):
        file_name, line, func, _, _ = inspect.getframeinfo(inspect.currentframe().f_back)
        logger.bind(name=Config.PITY_ERROR, func=func, line=line,
                    business=self.business, filename=file_name).exception(message)

    def json_error(self, error: str, hint: str = "", traceback_str: str = "",
                   file_name: str = None, line: int = None, func: str = None, **kwargs):
        """
        统一 JSON 格式记录错误日志

        :param error: 错误信息
        :param hint: 修复建议
        :param traceback_str: 堆栈信息
        :param file_name: 文件名（可选，默认自动获取）
        :param line: 行号（可选，默认自动获取）
        :param func: 函数名（可选，默认自动获取）
        :param kwargs: 其他自定义字段
        """
        if file_name is None:
            file_name, line, func, _, _ = inspect.getframeinfo(inspect.currentframe().f_back)
        log_data = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%SSS"),
            "level": "ERROR",
            "module": self.business,
            "file": file_name,
            "function": func,
            "line": line,
            "error": error,
            "hint": hint,
            "traceback": traceback_str,
            **kwargs,
        }
        message = json.dumps(log_data, ensure_ascii=False)
        logger.bind(name=Config.PITY_ERROR, func=func, line=line,
                    business=self.business, filename=file_name).error(message)

    def json_exception(self, error: str, hint: str = "", **kwargs):
        """
        统一 JSON 格式记录异常日志（自动捕获堆栈，直接写文件）

        :param error: 错误信息
        :param hint: 修复建议
        :param kwargs: 其他自定义字段
        """
        # 获取真实调用位置的堆栈
        import sys
        exc_info = sys.exc_info()
        tb_obj = exc_info[2]
        if tb_obj:
            frame = tb_obj.tb_frame
            file_name = frame.f_code.co_filename
            line = tb_obj.tb_lineno
            func = frame.f_code.co_name
        else:
            file_name, line, func, _, _ = inspect.getframeinfo(inspect.currentframe().f_back)
        traceback_str = "".join(tb.format_exception(*exc_info))
        log_data = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": "ERROR",
            "module": self.business,
            "file": file_name,
            "function": func,
            "line": line,
            "error": error,
            "hint": hint,
            "traceback": traceback_str,
            **kwargs,
        }
        # 直接写入 JSON 文件，不经过 loguru
        json_log_path = os.path.join(Config.LOG_DIR, "pity_error_json.log")
        with open(json_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
