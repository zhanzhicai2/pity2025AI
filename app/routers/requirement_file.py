"""
需求文件路由（上传/列表/删除）
"""
import os
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, Form
from typing import Optional

from app.crud.requirement_document import RequirementDocumentDao
from app.crud.requirement_file import RequirementFileDao
from app.exception.error import ParamsError
from app.handler.fatcory import PityResponse
from app.models.requirement_file import RequirementFile
from app.routers import Permission
from app.utils.logger import Log

router = APIRouter(prefix="/requirement/file", tags=["需求文件管理"])
logger = Log("requirement_file_router")

# 本地文件存储目录（当前使用本地存储，后续可接入 OSS，替换 save_path 逻辑即可）
# 如需使用 OSS：参考 app/routers/oss/oss_file.py 中的 OssClient.get_oss_client()
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads", "requirement")


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_current_user(user_info=Depends(Permission())):
    return user_info


@router.get("/{requirement_id}")
async def list_files(
    requirement_id: int,
    user_info: dict = Depends(get_current_user),
):
    """获取需求文档下的文件列表"""
    files = await RequirementFileDao.list_files(requirement_id=requirement_id)
    return PityResponse.success(files)


@router.post("/upload")
async def upload_file(
    requirement_id: int = Form(..., description="需求文档ID"),
    description: Optional[str] = Form(None, description="文件描述"),
    is_public: bool = Form(True, description="是否公开"),
    file: UploadFile = File(...),
    user_info: dict = Depends(get_current_user),
):
    """上传文件到需求文档"""
    # 验证需求文档存在
    doc = await RequirementDocumentDao.get_by_id(document_id=requirement_id)
    if not doc:
        raise ParamsError("需求文档不存在")

    ensure_upload_dir()

    # 获取文件扩展名
    original_name = file.filename or "unknown"
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""

    # 生成唯一文件名，保留原始名称
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    # 读取并保存文件
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    file_size = len(content)

    # 创建文件记录
    record = RequirementFile(
        user=user_info['id'],
        requirement_id=requirement_id,
        file_name=original_name,
        file_path=save_path,
        file_size=file_size,
        file_type=ext,
        description=description,
        is_public=is_public,
    )
    result = await RequirementFileDao.insert(model=record)
    return PityResponse.success(result)


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    user_info: dict = Depends(get_current_user),
):
    """删除需求文件"""
    file_record = await RequirementFileDao.delete_file(file_id, user_info['id'])
    if not file_record:
        raise ParamsError("文件不存在")

    # 删除本地物理文件
    if file_record.file_path and os.path.exists(file_record.file_path):
        try:
            os.remove(file_record.file_path)
        except OSError:
            logger.warning(f"删除物理文件失败: {file_record.file_path}")

    return PityResponse.success(msg="删除成功")
