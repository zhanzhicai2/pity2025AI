from typing import Tuple

from sqlalchemy import INT, Column, String, Boolean, JSON, Text, BIGINT, TIMESTAMP

from app.models import Base


class TestSuite(Base):
    """测试套件"""
    __tablename__ = "pity_test_suite"
    __allow_unmapped__ = True

    id = Column(INT, primary_key=True, comment='主键ID')
    name = Column(String(128), nullable=False, comment="套件名称")
    description = Column(Text, nullable=True, comment="描述")
    project_id = Column(INT, nullable=False, comment="关联项目 ID")
    env_id = Column(INT, nullable=True, comment="执行环境 ID")
    execution_mode = Column(String(16), nullable=False, default="sequential", comment="执行模式: sequential/parallel")
    retry_on_failure = Column(Boolean, nullable=False, default=False, comment="失败自动重试")
    stop_on_failure = Column(Boolean, nullable=False, default=False, comment="失败停止后续")
    notify_on_failure = Column(Boolean, nullable=False, default=False, comment="失败通知")
    created_at = Column(TIMESTAMP, nullable=False, comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    create_user = Column(INT, nullable=False, comment='创建人ID')
    update_user = Column(INT, nullable=False, comment='更新人ID')

    __fields__: Tuple[Column] = (id,)
    __tag__ = "测试套件"
    __alias__ = dict(name="套件名称")


class TestSuiteCase(Base):
    """测试套件-用例关联"""
    __tablename__ = "pity_test_suite_case"
    __allow_unmapped__ = True

    id = Column(INT, primary_key=True, comment='主键ID')
    suite_id = Column(INT, nullable=False, comment="关联套件 ID")
    case_id = Column(INT, nullable=False, comment="关联用例 ID")
    order = Column(INT, nullable=False, default=0, comment="执行顺序")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    timeout = Column(INT, nullable=True, comment="超时时间（秒）")
    retry = Column(INT, nullable=False, default=0, comment="重试次数")
    created_at = Column(TIMESTAMP, nullable=False, comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    create_user = Column(INT, nullable=False, comment='创建人ID')
    update_user = Column(INT, nullable=False, comment='更新人ID')

    __fields__: Tuple[Column] = (id,)
    __tag__ = "套件用例"
    __alias__ = dict(suite_id="套件ID", case_id="用例ID")


class TestSuiteVariable(Base):
    """测试套件变量"""
    __tablename__ = "pity_test_suite_variable"
    __allow_unmapped__ = True

    id = Column(INT, primary_key=True, comment='主键ID')
    suite_id = Column(INT, nullable=False, comment="关联套件 ID")
    key = Column(String(128), nullable=False, comment="变量名")
    value = Column(Text, nullable=True, comment="变量值")
    var_type = Column(String(16), nullable=False, default="string", comment="类型: string/json/yaml")
    description = Column(String(256), nullable=True, comment="描述")
    created_at = Column(TIMESTAMP, nullable=False, comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    create_user = Column(INT, nullable=False, comment='创建人ID')
    update_user = Column(INT, nullable=False, comment='更新人ID')

    __fields__: Tuple[Column] = (id,)
    __tag__ = "套件变量"
    __alias__ = dict(suite_id="套件ID", key="变量名")


class TestSuiteExecution(Base):
    """测试套件执行记录"""
    __tablename__ = "pity_test_suite_execution"
    __allow_unmapped__ = True

    id = Column(INT, primary_key=True, comment='主键ID')
    suite_id = Column(INT, nullable=False, comment="关联套件 ID")
    trace_id = Column(String(64), nullable=True, comment="追踪 ID")
    status = Column(String(16), nullable=False, default="pending", comment="状态: pending/running/success/failed")
    total_cases = Column(INT, nullable=False, default=0, comment="总用例数")
    passed = Column(INT, nullable=False, default=0, comment="通过数")
    failed = Column(INT, nullable=False, default=0, comment="失败数")
    error = Column(INT, nullable=False, default=0, comment="错误数")
    start_time = Column(TIMESTAMP, nullable=True, comment="开始时间")
    end_time = Column(TIMESTAMP, nullable=True, comment="结束时间")
    executor = Column(INT, nullable=True, comment="执行人 ID")
    created_at = Column(TIMESTAMP, nullable=False, comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    create_user = Column(INT, nullable=False, comment='创建人ID')
    update_user = Column(INT, nullable=False, comment='更新人ID')

    __fields__: Tuple[Column] = (id,)
    __tag__ = "套件执行"
    __alias__ = dict(suite_id="套件ID", status="状态")
