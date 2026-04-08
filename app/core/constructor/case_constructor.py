import json

from app.core.constructor.constructor import ConstructorAbstract
from app.crud.test_case.TestCaseDao import TestCaseDao
from app.models.constructor import Constructor


class TestcaseConstructor(ConstructorAbstract):

    @staticmethod
    async def run(executor, env, index, path, params, constructor: Constructor, **kwargs):
        try:
            data = json.loads(constructor.constructor_json)
            case_id = data.get("constructor_case_id")
            if not case_id:
                raise Exception("未获取到前/后置条件的用例id, 请检查前置条件")
            testcase = await TestCaseDao.async_query_test_case(case_id)
            executor.append(f"当前路径: {path}, 第{index + 1}条{ConstructorAbstract.get_name(constructor)}")

            # 检测循环嵌套：如果路径中已包含当前用例名，说明存在循环调用
            if f"->{testcase.name}" in path:
                raise Exception(f"检测到循环嵌套调用！用例 [{testcase.name}] 在其自身的调用路径中再次被调用，请检查该用例的前/后置条件配置")

            # 说明是case
            executor_class = kwargs.get('executor_class')(executor.logger)
            new_param = data.get("params")
            if new_param:
                temp = json.loads(new_param)
                params.update(temp)
            result, err = await executor_class.run(env, case_id, params, None, f"{path}->{testcase.name}")
            if err:
                raise Exception(err)
            if not result["status"]:
                raise Exception(f"断言失败, 断言数据: {result.get('asserts', 'unknown')}")
            return result
        except Exception as e:
            raise Exception(
                f"{path}->{constructor.name} 第{index + 1}个{ConstructorAbstract.get_name(constructor)}执行失败: {e}")
