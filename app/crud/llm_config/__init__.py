"""
LLM 配置 DAO 层
"""
from typing import Optional, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import Mapper, ModelWrapper
from app.models import async_session
from app.models.llm_config import LLMConfig


@ModelWrapper(LLMConfig)
class LLMConfigDao(Mapper):
    """LLM 配置数据访问对象"""

    @classmethod
    async def list_configs(
        cls,
        provider: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[LLMConfig]:
        """获取配置列表"""
        async with async_session() as session:
            query = select(LLMConfig).where(LLMConfig.deleted_at == 0)

            if provider:
                query = query.where(LLMConfig.provider == provider)

            if is_active is not None:
                query = query.where(LLMConfig.is_active == is_active)

            query = query.order_by(LLMConfig.is_default.desc(), LLMConfig.id.desc())

            result = await session.execute(query)
            return list(result.scalars().all())

    @classmethod
    async def get_by_id(cls, config_id: int) -> Optional[LLMConfig]:
        """根据ID获取配置"""
        async with async_session() as session:
            query = select(LLMConfig).where(
                LLMConfig.id == config_id,
                LLMConfig.deleted_at == 0
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_default(cls) -> Optional[LLMConfig]:
        """获取默认配置"""
        async with async_session() as session:
            query = select(LLMConfig).where(
                LLMConfig.is_default == True,
                LLMConfig.is_active == True,
                LLMConfig.deleted_at == 0
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def insert(cls, model: LLMConfig) -> LLMConfig:
        """插入配置"""
        async with async_session() as session:
            session.add(model)
            await session.flush()
            await session.commit()
            await session.refresh(model)
            return model

    @classmethod
    async def update_config(cls, config_id: int, user_id: int, **kwargs) -> Optional[LLMConfig]:
        """更新配置"""
        async with async_session() as session:
            kwargs['updated_at'] = __import__('datetime').datetime.now()
            kwargs['update_user'] = user_id

            stmt = (
                update(LLMConfig)
                .where(LLMConfig.id == config_id, LLMConfig.deleted_at == 0)
                .values(**kwargs)
            )
            await session.execute(stmt)
            await session.commit()

            # 重新查询获取更新后的数据
            query = select(LLMConfig).where(LLMConfig.id == config_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def unset_all_defaults(cls):
        """取消所有默认配置"""
        async with async_session() as session:
            stmt = (
                update(LLMConfig)
                .where(LLMConfig.is_default == True, LLMConfig.deleted_at == 0)
                .values(is_default=False)
            )
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def set_default(cls, config_id: int) -> Optional[LLMConfig]:
        """设置为默认配置"""
        async with async_session() as session:
            # 检查配置是否存在
            query = select(LLMConfig).where(LLMConfig.id == config_id, LLMConfig.deleted_at == 0)
            result = await session.execute(query)
            config = result.scalar_one_or_none()
            if not config:
                return None

            # 取消所有默认配置
            unset_stmt = (
                update(LLMConfig)
                .where(LLMConfig.is_default == True, LLMConfig.deleted_at == 0)
                .values(is_default=False)
            )
            await session.execute(unset_stmt)

            # 设置当前配置为默认
            set_stmt = (
                update(LLMConfig)
                .where(LLMConfig.id == config_id)
                .values(is_default=True)
            )
            await session.execute(set_stmt)
            await session.commit()

            # 重新查询
            query = select(LLMConfig).where(LLMConfig.id == config_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def delete_config(cls, config_id: int, user_id: int) -> bool:
        """删除配置（逻辑删除）"""
        async with async_session() as session:
            # 检查配置是否存在
            query = select(LLMConfig).where(LLMConfig.id == config_id, LLMConfig.deleted_at == 0)
            result = await session.execute(query)
            config = result.scalar_one_or_none()
            if not config:
                return False

            # 逻辑删除
            stmt = (
                update(LLMConfig)
                .where(LLMConfig.id == config_id)
                .values(
                    deleted_at=int(__import__('time').time() * 1000),
                    update_user=user_id
                )
            )
            await session.execute(stmt)
            await session.commit()
            return True
