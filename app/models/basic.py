import json
from datetime import datetime
from decimal import Decimal
from typing import Tuple

from sqlalchemy import INT, Column, BIGINT, TIMESTAMP

from app.models import Base
from config import Config


class PityBase(Base):
    __abstract__ = True
    __allow_unmapped__ = True
    id = Column(INT, primary_key=True, comment='主键ID')
    created_at = Column(TIMESTAMP, nullable=False, comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    create_user = Column(INT, nullable=False, comment='创建人ID')
    update_user = Column(INT, nullable=False, comment='更新人ID')
    __fields__: Tuple[Column] = [id]
    __tag__ = "未定义"
    __alias__ = dict(name="名称")
    __show__ = 1

    def __init__(self, user, id=None):
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.create_user = user
        self.update_user = user
        self.deleted_at = 0
        # self.id = id

    def serialize(self, *ignore):
        """
        dump self
        :return:
        """
        data = dict()
        for c in self.__table__.columns:
            if c.name in ignore:
                # 如果字段忽略, 则不进行转换
                continue
            val = getattr(self, c.name)
            if isinstance(val, datetime):
                data[c.name] = val.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(val, Decimal):
                data[c.name] = str(val)
            elif isinstance(val, bytes):
                data[c.name] = val.decode(encoding='utf-8')
            else:
                data[c.name] = val
        return json.dumps(data, ensure_ascii=False)


class PityRelationField(object):
    def __init__(self, field, foreign=None):
        self.field = field
        self.foreign = foreign


def init_relation(model, *data: PityRelationField):
    setattr(model, Config.RELATION, data)
