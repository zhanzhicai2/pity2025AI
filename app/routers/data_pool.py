"""
数据池 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.data_pool import get_tool_list, get_tool_categories, generate_data
from app.crud.data_pool.DataPoolDao import DataPoolDao
from app.middleware.Auth import Permission
from app.schema.data_pool import (
    DataPoolRecordForm,
    DataPoolGenerateForm,
    DataPoolBatchGenerateForm,
    DataPoolFavoriteForm,
)
from app.utils.logger import Log

logger = Log("data_pool_router")
router = APIRouter(prefix="/data-pool", tags=["数据池"])


def get_current_user(user_info=Depends(Permission())):
    """获取当前用户"""
    return user_info


@router.get("/tools", summary="获取工具列表")
async def list_tools():
    """获取所有可用的数据生成工具"""
    categories = get_tool_categories()
    return {"code": 0, "data": categories, "msg": "success"}


@router.post("/generate", summary="生成单条数据")
async def generate_single_data(form: DataPoolGenerateForm, user_info: dict = Depends(get_current_user)):
    """生成单条测试数据"""
    try:
        user_id = user_info.get("id")
        # 生成数据
        result = generate_data(form.tool_name, form.params)

        # 保存到记录
        record_form = DataPoolRecordForm(
            tool_name=form.tool_name,
            tool_category="test_data",
            input_data=form.params,
            output_data=result
        )
        record = await DataPoolDao.insert_record(record_form, user_id)

        return {"code": 0, "data": {"record_id": record.id, "result": result}, "msg": "success"}
    except ValueError as e:
        return {"code": 110, "data": None, "msg": str(e)}
    except Exception as e:
        logger.error(f"生成数据失败: {e}")
        return {"code": 110, "data": None, "msg": f"生成数据失败: {str(e)}"}


@router.post("/batch-generate", summary="批量生成数据")
async def batch_generate_data(form: DataPoolBatchGenerateForm, user_info: dict = Depends(get_current_user)):
    """批量生成测试数据"""
    try:
        user_id = user_info.get("id")
        results = []
        for _ in range(form.count):
            result = generate_data(form.tool_name, form.params)
            results.append(result)

            # 保存到记录
            record_form = DataPoolRecordForm(
                tool_name=form.tool_name,
                tool_category="test_data",
                input_data=form.params,
                output_data=result
            )
            await DataPoolDao.insert_record(record_form, user_id)

        return {"code": 0, "data": results, "msg": "success"}
    except ValueError as e:
        return {"code": 110, "data": None, "msg": str(e)}
    except Exception as e:
        logger.error(f"批量生成数据失败: {e}")
        return {"code": 110, "data": None, "msg": f"批量生成数据失败: {str(e)}"}


@router.get("/records", summary="获取使用记录")
async def list_records(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tool_name: Optional[str] = None,
    tool_category: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    user_info: dict = Depends(get_current_user)
):
    """获取数据使用记录"""
    try:
        user_id = user_info.get("id")
        records, total = await DataPoolDao.list_records(
            user_id=user_id,
            page=page,
            size=size,
            tool_name=tool_name,
            tool_category=tool_category,
            is_favorite=is_favorite
        )

        # 转换为 dict
        data = []
        for r in records:
            data.append({
                "id": r.id,
                "tool_name": r.tool_name,
                "tool_category": r.tool_category,
                "input_data": r.input_data,
                "output_data": r.output_data,
                "tags": r.tags,
                "is_favorite": r.is_favorite,
                "created_at": r.created_at.isoformat() if r.created_at else None
            })

        return {
            "code": 0,
            "data": {
                "list": data,
                "total": total,
                "page": page,
                "size": size
            },
            "msg": "success"
        }
    except Exception as e:
        logger.error(f"查询记录失败: {e}")
        return {"code": 110, "data": None, "msg": f"查询记录失败: {str(e)}"}


@router.delete("/records/{record_id}", summary="删除记录")
async def delete_record(record_id: int, user_info: dict = Depends(get_current_user)):
    """删除数据使用记录（软删除）"""
    try:
        user_id = user_info.get("id")
        await DataPoolDao.delete_record(record_id, user_id)
        return {"code": 0, "data": None, "msg": "删除成功"}
    except Exception as e:
        logger.error(f"删除记录失败: {e}")
        return {"code": 110, "data": None, "msg": f"删除记录失败: {str(e)}"}


@router.post("/favorite", summary="收藏/取消收藏")
async def favorite_record(form: DataPoolFavoriteForm, user_info: dict = Depends(get_current_user)):
    """收藏或取消收藏记录"""
    try:
        user_id = user_info.get("id")
        record = await DataPoolDao.favorite_record(form.id, user_id, form.is_favorite)
        return {"code": 0, "data": {"id": record.id, "is_favorite": record.is_favorite}, "msg": "success"}
    except Exception as e:
        logger.error(f"收藏记录失败: {e}")
        return {"code": 110, "data": None, "msg": f"收藏记录失败: {str(e)}"}
