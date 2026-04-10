from sqlalchemy import Column, String, INT, TEXT, Boolean

from app.models.basic import PityBase


class MockRule(PityBase):
    """Mock 规则"""
    __tablename__ = "pity_mock_rule"

    name = Column(String(64), comment='规则名称')
    description = Column(TEXT, comment='描述')
    project_id = Column(INT, comment='关联项目ID')

    # 匹配条件
    url_pattern = Column(String(256), comment='URL 正则匹配')
    method = Column(String(10), comment='请求方法')

    # 响应内容
    response_status = Column(INT, default=200, comment='HTTP 状态码')
    response_body = Column(TEXT, comment='响应体')
    response_headers = Column(TEXT, comment='响应头 JSON')
    response_delay = Column(INT, default=0, comment='延迟 ms')

    # 条件匹配（可选）
    request_headers = Column(TEXT, comment='请求头条件 JSON')
    request_body_pattern = Column(String(256), comment='请求体正则')

    is_active = Column(Boolean, default=True, comment='是否启用')

    __table_args__ = (
        {'comment': 'Mock 规则表', 'mysql_charset': 'utf8mb4'},
    )
    __fields__ = [name, project_id, url_pattern, method, response_status, is_active]
    __tag__ = "Mock规则"
    __alias__ = dict(
        name="规则名称",
        project_id="项目",
        url_pattern="URL模式",
        method="请求方法",
        response_status="状态码",
        response_delay="延迟",
        is_active="启用状态"
    )

    def __init__(self, name, project_id, url_pattern, method, create_user,
                 description=None, response_status=200, response_body="",
                 response_headers=None, response_delay=0, request_headers=None,
                 request_body_pattern=None, is_active=True, id=None):
        super().__init__(create_user, id)
        self.name = name
        self.project_id = project_id
        self.description = description
        self.url_pattern = url_pattern
        self.method = method
        self.response_status = response_status
        self.response_body = response_body
        self.response_headers = response_headers or "{}"
        self.response_delay = response_delay
        self.request_headers = request_headers or "{}"
        self.request_body_pattern = request_body_pattern
        self.is_active = is_active

    def __str__(self):
        return f"[Mock规则: {self.name}]({self.id})"
