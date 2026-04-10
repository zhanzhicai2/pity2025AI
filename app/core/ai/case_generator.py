"""
AI 用例生成器 - Phase X 核心
自动解析需求、创建目录、生成用例
"""
import json
import re
from typing import List, Dict, Any, Optional

from app.core.ai.base import AIService
from app.crud.ai_generation_task.AIGenerationTaskDao import AIGenerationTaskDao
from app.crud.testcase_directory.TestcaseDirectoryDao import TestcaseDirectoryDao
from app.models.ai_generation_task import PityAIGenerationTask
from app.utils.logger import Log


class ModuleResolver:
    """模块解析器 - 从需求中识别模块"""
    log = Log("ModuleResolver")

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def parse_modules(self, requirement: str, project_id: int) -> List[Dict[str, Any]]:
        """
        解析需求文本，识别出模块列表
        返回: [{"name": "登录模块", "description": "用户登录相关功能"}, ...]
        """
        prompt = f"""从以下需求中识别出模块（功能模块）名称列表，返回JSON数组格式：
需求：{requirement}

要求：
1. 识别出主要的功能模块
2. 每个模块包含 name（模块名称）和 description（模块描述）
3. 返回格式如：[{{"name": "登录模块", "description": "用户登录相关功能"}}, ...]
4. 只返回JSON数组，不要其他内容
5. 如果需求中只有一个模块，也返回数组格式
"""

        try:
            response = await self.ai_service.chat(prompt)
            # 解析 JSON 响应
            text = response.get("content", "")
            # 提取 JSON 部分
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                modules = json.loads(json_match.group())
                return modules
            return []
        except Exception as e:
            self.log.error(f"解析模块失败: {e}")
            return []


class DirectoryManager:
    """目录管理器 - 自动创建/复用目录"""
    log = Log("DirectoryManager")

    def __init__(self, project_id: int, user_id: int):
        self.project_id = project_id
        self.user_id = user_id
        self.created_dirs = []  # 记录本次创建的目录

    async def get_or_create_directory(self, module_name: str, parent: int = None) -> int:
        """
        获取或创建目录
        如果目录已存在则复用，不存在则自动创建
        返回: directory_id
        """
        from app.models.testcase_directory import PityTestcaseDirectory

        # 查询目录是否已存在
        existing = await TestcaseDirectoryDao.query_record(
            project_id=self.project_id,
            name=module_name,
            parent=parent or 0,
        )

        if existing:
            self.log.info(f"目录已存在，复用: {module_name} (id={existing.id})")
            return existing.id

        # 创建新目录（使用 Form 格式）
        from app.schema.testcase_directory import PityTestcaseDirectoryForm
        form = PityTestcaseDirectoryForm(
            project_id=self.project_id,
            name=module_name,
            parent=parent,
        )
        model = PityTestcaseDirectory(form=form, user=self.user_id)
        result = await TestcaseDirectoryDao.insert(model=model, log=True)
        self.created_dirs.append({"name": module_name, "id": result.id})
        self.log.info(f"目录已创建: {module_name} (id={result.id})")
        return result.id

    async def get_or_create_directories(self, modules: List[Dict]) -> List[Dict]:
        """批量获取或创建目录"""
        result = []
        for module in modules:
            dir_id = await self.get_or_create_directory(module.get("name"))
            result.append({
                "name": module.get("name"),
                "directory_id": dir_id,
                "description": module.get("description", ""),
                "created": dir_id not in [m.get("id") for m in self.created_dirs] if self.created_dirs else True
            })
        return result


class CaseGenerator:
    """用例生成器 - 根据模板和需求生成用例"""
    log = Log("CaseGenerator")

    def __init__(self, ai_service: AIService, user_id: int):
        self.ai_service = ai_service
        self.user_id = user_id

    async def generate_cases_for_module(
        self,
        module_name: str,
        template_id: int,
        case_type: str,
        directory_id: int,
        project_id: int,
        case_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        为单个模块生成用例
        返回: 生成用例的列表
        """
        # 获取模板信息
        from app.crud.testcase_template.TestcaseTemplateDao import TestcaseTemplateDao
        template = await TestcaseTemplateDao.query_record(id=template_id)
        if not template:
            self.log.error(f"模板不存在: {template_id}")
            return []

        # 构建生成 prompt
        prompt = self._build_generation_prompt(
            module_name=module_name,
            field_mapping=template.field_mapping,
            case_type=case_type,
            case_count=case_count
        )

        try:
            response = await self.ai_service.chat(prompt)
            text = response.get("content", "")
            # 提取用例数据
            cases = self._parse_cases(text, template.field_mapping)
            return cases
        except Exception as e:
            self.log.error(f"生成用例失败: {e}")
            return []

    def _build_generation_prompt(
        self,
        module_name: str,
        field_mapping: Dict,
        case_type: str,
        case_count: int
    ) -> str:
        """构建用例生成 prompt"""
        # 提取字段定义
        columns = field_mapping.get("columns", [])
        field_descriptions = []
        for col in columns:
            required = "必填" if col.get("required") else "可选"
            field_descriptions.append(f"- {col.get('label')}({col.get('name')}): {col.get('description', '')} [{required}]")

        fields_text = "\n".join(field_descriptions)

        prompt = f"""为"{module_name}"模块生成 {case_count} 条测试用例。

用例类型: {case_type}

模板字段定义：
{fields_text}

要求：
1. 生成 {case_count} 条具有代表性的测试用例
2. 每条用例应覆盖不同的测试场景
3. 返回JSON数组格式，每条用例包含所有字段的值
4. 字段名使用 field_mapping 中定义的 name
5. 只返回JSON数组，不要其他内容

返回格式：
[{{"field_name": "value", ...}}, ...]
"""
        return prompt

    def _parse_cases(self, text: str, field_mapping: Dict) -> List[Dict[str, Any]]:
        """解析 AI 返回的用例文本"""
        try:
            # 提取 JSON 部分
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                cases = json.loads(json_match.group())
                return cases
            return []
        except Exception as e:
            self.log.error(f"解析用例失败: {e}")
            return []

    async def save_cases(
        self,
        cases: List[Dict[str, Any]],
        module_info: Dict,
        template_id: int,
        case_type: str,
        directory_id: int,
        task_id: int,
        project_id: int
    ) -> int:
        """
        保存生成的用例到数据库
        返回: 成功保存的用例数量
        """
        saved_count = 0

        for case_data in cases:
            try:
                # 构建用例数据
                from app.models.case_v2 import PityCaseV2
                from app.crud.case_v2.CaseV2Dao import CaseV2Dao

                model = PityCaseV2(
                    name=case_data.get("name", case_data.get("case_name", "未命名")),
                    case_no=case_data.get("case_no"),
                    priority=case_data.get("priority", "P2"),
                    status=1,
                    directory_id=directory_id,
                    tag=case_data.get("tag", ""),
                    template_id=template_id,
                    case_type=case_type,
                    source="ai",
                    preconditions=case_data.get("preconditions", ""),
                    expected_result=case_data.get("expected_result", ""),
                    test_steps=case_data.get("test_steps", ""),
                    parent_task_id=task_id,
                    create_user=self.user_id,
                )
                result = await CaseV2Dao.insert(model=model, log=True)

                # 保存扩展字段
                await self._save_case_fields(result.id, case_data, template_id)

                saved_count += 1
            except Exception as e:
                self.log.error(f"保存用例失败: {e}")

        return saved_count

    async def _save_case_fields(self, case_id: int, case_data: Dict, template_id: int):
        """保存用例的扩展字段"""
        from app.models.case_field import PityTestcaseField
        from app.crud import async_session

        # 获取模板字段定义
        from app.crud.testcase_template.TestcaseTemplateDao import TestcaseTemplateDao
        template = await TestcaseTemplateDao.query_record(id=template_id)
        if not template:
            return

        field_mapping = template.field_mapping
        columns = field_mapping.get("columns", [])

        # 获取标准字段（name, case_no, priority 等在主表，不需要存扩展字段）
        standard_fields = {"name", "case_no", "priority", "status", "tag", "preconditions", "expected_result", "test_steps"}

        # 只保存模板自定义的扩展字段
        async with async_session() as session:
            for col in columns:
                field_name = col.get("name")
                if field_name in standard_fields:
                    continue
                if field_name in case_data:
                    field_model = PityTestcaseField(
                        case_id=case_id,
                        field_name=field_name,
                        field_value=str(case_data[field_name]),
                        create_user=self.user_id,
                    )
                    session.add(field_model)
            await session.commit()


class AIGenerationWorkflow:
    """AI 生成工作流 - 串联整个生成过程"""

    def __init__(self, user_id: int, ai_service: AIService = None):
        self.user_id = user_id
        self.ai_service = ai_service or self._create_ai_service()

    def _create_ai_service(self):
        """创建 AI 服务实例"""
        from app.core.ai.factory import AIServiceFactory
        factory = AIServiceFactory()
        return factory.create_service()

    async def execute(self, task_id: int) -> Dict[str, Any]:
        """
        执行完整的 AI 生成工作流
        1. 获取任务信息
        2. 解析模块
        3. 创建/复用目录
        4. 生成用例
        5. 更新任务状态
        """
        # 获取任务信息
        task = await AIGenerationTaskDao.query_record(id=task_id)
        if not task:
            return {"status": "error", "message": f"任务不存在: {task_id}"}

        try:
            # 更新状态为解析中
            await self._update_task_status(task_id, "parsing", 0)

            # 1. 解析模块
            resolver = ModuleResolver(self.ai_service)
            modules = await resolver.parse_modules(task.requirement, task.project_id)

            if not modules:
                await self._update_task_status(task_id, "failed", 0, error="无法解析需求中的模块")
                return {"status": "error", "message": "无法解析模块"}

            # 2. 创建/复用目录
            dir_manager = DirectoryManager(task.project_id, self.user_id)
            module_dirs = await dir_manager.get_or_create_directories(modules)

            # 更新任务进度
            total_cases = len(modules) * 5  # 假设每个模块生成 5 条用例
            await self._update_task_progress(task_id, module_count=len(modules), total_cases=total_cases)

            # 3. 生成用例
            generator = CaseGenerator(self.ai_service, self.user_id)
            total_generated = 0

            for module_dir in module_dirs:
                # 更新状态为生成中
                await self._update_task_status(task_id, "generating", int(total_generated / total_cases * 100))

                # 生成用例
                cases = await generator.generate_cases_for_module(
                    module_name=module_dir["name"],
                    template_id=task.template_id,
                    case_type=task.case_type,
                    directory_id=module_dir["directory_id"],
                    project_id=task.project_id,
                    case_count=5
                )

                # 保存用例
                saved = await generator.save_cases(
                    cases=cases,
                    module_info=module_dir,
                    template_id=task.template_id,
                    case_type=task.case_type,
                    directory_id=module_dir["directory_id"],
                    task_id=task_id,
                    project_id=task.project_id
                )
                total_generated += saved

            # 4. 完成
            await self._update_task_status(task_id, "completed", 100,
                                         generated_cases=total_generated,
                                         modules=module_dirs)

            return {
                "status": "completed",
                "message": f"生成完成，共 {total_generated} 条用例",
                "modules": module_dirs,
                "generated_cases": total_generated
            }

        except Exception as e:
            self.log.error(f"AI 生成失败: {e}")
            await self._update_task_status(task_id, "failed", 0, error=str(e))
            return {"status": "error", "message": str(e)}

    async def _update_task_status(
        self,
        task_id: int,
        status: str,
        progress: int = None,
        generated_cases: int = None,
        modules: List = None,
        error: str = None
    ):
        """更新任务状态"""
        from app.crud.ai_generation_task.AIGenerationTaskDao import AIGenerationTaskDao
        from app.models.ai_generation_task import PityAIGenerationTask

        update_data = {"status": status}
        if progress is not None:
            update_data["progress"] = progress
        if generated_cases is not None:
            update_data["generated_cases"] = generated_cases
        if modules is not None:
            update_data["modules"] = json.dumps(modules, ensure_ascii=False)
        if error:
            update_data["error"] = error

        await AIGenerationTaskDao.update_by_map(
            self.user_id,
            PityAIGenerationTask.id == task_id,
            **update_data
        )

    async def _update_task_progress(self, task_id: int, module_count: int = None, total_cases: int = None):
        """更新任务进度"""
        from app.crud.ai_generation_task.AIGenerationTaskDao import AIGenerationTaskDao
        from app.models.ai_generation_task import PityAIGenerationTask

        update_data = {}
        if module_count is not None:
            update_data["module_count"] = module_count
        if total_cases is not None:
            update_data["total_cases"] = total_cases

        if update_data:
            await AIGenerationTaskDao.update_by_map(
                self.user_id,
                PityAIGenerationTask.id == task_id,
                **update_data
            )
