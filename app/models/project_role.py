from sqlalchemy import INT, Column

from app.models.basic import PityBase


class ProjectRole(PityBase):
    __tablename__ = 'pity_project_role'
    __table_args__ = {'comment': '项目角色表', 'mysql_charset': 'utf8mb4'}

    user_id = Column(INT, index=True, comment='用户ID')
    project_id = Column(INT, index=True, comment='项目ID')
    project_role = Column(INT, index=True, comment='项目角色 0:组员 1:组长 2:负责人')
    __alias__ = dict(user_id="用户", project_id="项目", project_role="角色")
    __tag__ = "项目角色"
    __fields__ = (project_id, user_id, project_role)
    __show__ = 2

    def __init__(self, user_id, project_id, project_role, create_user):
        super().__init__(create_user)
        self.user_id = user_id
        self.project_id = project_id
        self.project_role = project_role
