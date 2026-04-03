from fastapi import Depends

from app.handler.fatcory import PityResponse
from app.routers import Permission
from app.routers.online.sql import router
from app.schema.script import PyScriptForm

tag = "Python脚本"

# 允许的内置函数白名单
ALLOWED_BUILTINS = {
    'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set',
    'range', 'enumerate', 'zip', 'map', 'filter', 'sum', 'min', 'max',
    'abs', 'round', 'pow', 'sorted', 'reversed', 'any', 'all', 'isinstance',
    'type', 'print', 'open', 'json', 'time', 'datetime', 'timedelta',
}


@router.post("/script")
def execute_py_script(data: PyScriptForm, _=Depends(Permission())):
    """
    执行 Python 脚本（安全限制版）
    注意：此功能风险较高，仅限于管理员使用
    """
    try:
        loc = dict()
        # 限制可用的内置函数，防止危险操作
        allowed_builtins = {k: __builtins__.__dict__.get(k) for k in ALLOWED_BUILTINS if k in __builtins__.__dict__}
        exec(data.command, {'__builtins__': allowed_builtins}, loc)
        value = loc.get(data.value)
        return PityResponse.success(data=value)
    except Exception as err:
        return PityResponse.failed(err)
