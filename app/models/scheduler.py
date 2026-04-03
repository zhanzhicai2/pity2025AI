from typing import Tuple

from sqlalchemy import INT, Column, String, Boolean, JSON, Text, BIGINT, TIMESTAMP

from app.models import Base


class PityPeriodicTask(Base):
    """周期任务配置表"""
    __tablename__ = "pity_periodic_task"
    __allow_unmapped__ = True

    id = Column(INT, primary_key=True, comment='主键ID')
    name = Column(String(64), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    task_type = Column(String(32), nullable=False, comment="任务类型: http/sql/redis/python/testcase/test_plan")
    task_config = Column(JSON, nullable=False, comment="任务配置 JSON")
    schedule_type = Column(String(16), nullable=False, comment="调度类型: crontab/interval")
    crontab_id = Column(INT, nullable=True, comment="关联的 Crontab 调度 ID")
    interval_id = Column(INT, nullable=True, comment="关联的 Interval 调度 ID")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    project_id = Column(INT, nullable=True, comment="关联项目 ID")
    notify_on_failure = Column(Boolean, nullable=False, default=False, comment="失败是否通知")
    max_instances = Column(INT, nullable=False, default=1, comment="最大并发实例数")
    created_at = Column(TIMESTAMP, nullable=False, comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    create_user = Column(INT, nullable=False, comment='创建人ID')
    update_user = Column(INT, nullable=False, comment='更新人ID')

    __fields__: Tuple[Column] = (id,)
    __tag__ = "定时任务"
    __alias__ = dict(name="任务名称")


class PityCrontabSchedule(Base):
    """Crontab 表达式表"""
    __tablename__ = "pity_crontab_schedule"
    __allow_unmapped__ = True

    id = Column(INT, primary_key=True, comment='主键ID')
    minute = Column(String(64), nullable=False, default="*", comment="分钟 (0-59, *)")
    hour = Column(String(64), nullable=False, default="*", comment="小时 (0-23, *)")
    day_of_week = Column(String(64), nullable=False, default="*", comment="星期 (0-6 或 mon-sun, *)")
    day_of_month = Column(String(64), nullable=False, default="*", comment="日期 (1-31, *)")
    month_of_year = Column(String(64), nullable=False, default="*", comment="月份 (1-12, *)")
    expression = Column(String(128), nullable=True, comment="原始 crontab 表达式")
    created_at = Column(TIMESTAMP, nullable=False, comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    create_user = Column(INT, nullable=False, comment='创建人ID')
    update_user = Column(INT, nullable=False, comment='更新人ID')

    __fields__: Tuple[Column] = (id,)
    __tag__ = "Crontab 调度"
    __alias__ = dict(expression="表达式")


class PityIntervalSchedule(Base):
    """间隔执行配置表"""
    __tablename__ = "pity_interval_schedule"
    __allow_unmapped__ = True

    id = Column(INT, primary_key=True, comment='主键ID')
    interval_type = Column(String(16), nullable=False, comment="间隔类型: seconds/minutes/hours/days/weeks")
    interval_value = Column(INT, nullable=False, comment="间隔数值")
    created_at = Column(TIMESTAMP, nullable=False, comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    create_user = Column(INT, nullable=False, comment='创建人ID')
    update_user = Column(INT, nullable=False, comment='更新人ID')

    __fields__: Tuple[Column] = (id,)
    __tag__ = "间隔调度"
    __alias__ = dict(interval_type="类型", interval_value="数值")


class PityTaskExecution(Base):
    """任务执行记录表"""
    __tablename__ = "pity_task_execution"
    __allow_unmapped__ = True

    id = Column(INT, primary_key=True, comment='主键ID')
    task_id = Column(INT, nullable=False, comment="关联的 PeriodicTask ID")
    trace_id = Column(String(64), nullable=True, comment="追踪 ID")
    status = Column(String(16), nullable=False, default="pending", comment="状态: pending/running/success/failed")
    start_time = Column(TIMESTAMP, nullable=True, comment="开始时间")
    end_time = Column(TIMESTAMP, nullable=True, comment="结束时间")
    result = Column(JSON, nullable=True, comment="执行结果 JSON")
    error_message = Column(Text, nullable=True, comment="错误信息")
    executor = Column(INT, nullable=True, comment="执行人 ID，0 表示系统执行")
    created_at = Column(TIMESTAMP, nullable=False, comment='创建时间')
    updated_at = Column(TIMESTAMP, nullable=False, comment='更新时间')
    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')
    create_user = Column(INT, nullable=False, comment='创建人ID')
    update_user = Column(INT, nullable=False, comment='更新人ID')

    __fields__: Tuple[Column] = (id,)
    __tag__ = "任务执行"
    __alias__ = dict(task_id="任务ID", status="状态")
