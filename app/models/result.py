from datetime import datetime

from sqlalchemy import INT, Column, TIMESTAMP, String, BIGINT
from sqlalchemy import SMALLINT
from sqlalchemy import TEXT

from app.models import Base


class PityTestResult(Base):
    __tablename__ = 'pity_test_result'

    id = Column(INT, primary_key=True, comment='主键ID')
    directory_id = None

    report_id = Column(INT, index=True, comment='报告ID')
    case_id = Column(INT, index=True, comment='用例ID')
    case_name = Column(String(32), comment='用例名称')

    status = Column(SMALLINT, comment="对应状态 0: 成功 1: 失败 2: 出错 3: 跳过")

    start_at = Column(TIMESTAMP, nullable=False, comment='开始时间')
    finished_at = Column(TIMESTAMP, nullable=False, comment='结束时间')

    case_log = Column(TEXT, comment='用例日志')

    retry = Column(INT, default=0, comment='重试次数')

    status_code = Column(INT, comment='HTTP状态码')

    url = Column(TEXT, comment='请求URL')

    body = Column(TEXT, comment='请求体')

    request_params = Column(TEXT, comment='请求参数')

    data_name = Column(String(24), comment='数据名称')

    data_id = Column(INT, comment='数据ID')

    request_method = Column(String(12), nullable=True, comment='请求方法')

    request_headers = Column(TEXT, comment='请求头')

    cost = Column(String(12), nullable=False, comment='耗时(ms)')

    asserts = Column(TEXT, comment='断言结果')

    response_headers = Column(TEXT, comment='响应头')

    response = Column(TEXT, comment='响应内容')

    cookies = Column(TEXT, comment='Cookies')

    deleted_at = Column(BIGINT, nullable=False, default=0, comment='删除时间戳')

    def __init__(self, report_id: int, case_id: int, case_name: str, status: int,
                 case_log: str, start_at: datetime, finished_at: datetime,
                 url: str, body: str, request_method: str, request_headers: str, cost: str,
                 asserts: str, response_headers: str, response: str,
                 status_code: int, cookies: str, retry: int = None,
                 request_params: str = '', data_name: str = '', data_id: int = None
                 ):
        self.report_id = report_id
        self.case_id = case_id
        self.case_name = case_name
        self.status = status
        self.case_log = case_log
        self.start_at = start_at
        self.finished_at = finished_at
        self.retry = retry
        self.status_code = status_code
        self.url = url
        self.request_method = request_method
        self.request_headers = request_headers
        self.body = body
        self.cost = cost
        self.response = response
        self.response_headers = response_headers
        self.asserts = asserts
        self.cookies = cookies
        self.request_params = request_params
        self.data_name = data_name
        self.data_id = data_id
        self.deleted_at = 0
