import json
from typing import Dict, List


class PromptTemplate:
    """AI Prompt 模板管理"""

    # 测试用例生成 Prompt
    GENERATE_CASE_TEMPLATE = """你是一个专业的 API 测试工程师。请根据以下 API 描述生成测试用例配置。

## 输出格式
请严格输出 JSON 格式，不要包含其他说明文字：

```json
{{
    "name": "用例名称（简洁，20字以内）",
    "url": "/api/path（相对路径）",
    "request_method": "GET|POST|PUT|DELETE|PATCH",
    "body_type": 0-5,  // 0=none, 1=json, 2=form, 3=x-www-form-urlencoded, 4=binary, 5=graphql
    "request_headers": {{"Content-Type": "application/json"}},
    "body": {{}},  // 请求体，JSON 格式
    "asserts": [
        {{
            "assert_type": "equal|in|contain|not_equal|json_equal|status_code",
            "expected": "预期值",
            "actually": "$.json.path（使用 JSONPath 引用响应字段）"
        }}
    ]
}}
```

## API 描述
{api_description}

## 要求
1. 用例名称要简洁明确，反映 API 的核心功能
2. URL 使用相对路径（不带域名）
3. 请求体中的测试数据要真实可用（用户名不要用 admin，密码用占位符如 ${password}）
4. 断言必须包含：
   - HTTP 状态码验证（status_code）
   - 业务状态码验证（如 code=0 表示成功）
5. 响应 JSONPath 格式：$.data.xxx 或 $.code
6. 如果是 GET 请求，body_type 设为 0，body 设为 {{}}
"""

    # 断言增强 Prompt
    ENHANCE_ASSERTS_TEMPLATE = """你是一个专业的 API 测试工程师。请根据以下信息生成或增强测试断言。

## 用例信息
- 名称：{case_name}
- URL：{url}
- 请求方法：{method}
- 请求体：{body}

## 响应示例
```json
{response_sample}
```

## 输出格式
请严格输出 JSON 数组格式：

```json
[
    {{
        "assert_type": "equal|contain|in|status_code|json_equal",
        "expected": "预期值",
        "actually": "$.json.path"
    }}
]
```

## 要求
1. 分析响应示例，识别关键字段
2. 断言必须包含：
   - HTTP 状态码（assert_type: status_code）
   - 业务状态码（assert_type: equal, expected: "0" 或 "200"）
   - 关键业务字段验证
3. 如果响应包含列表数据，验证列表非空或长度
4. JSONPath 使用 $. 前缀
"""

    # OpenAPI 批量生成 Prompt
    BATCH_GENERATE_TEMPLATE = """你是一个专业的 API 测试工程师。请从以下 OpenAPI 规范中生成测试用例列表。

## OpenAPI 规范
```json
{openapi_spec}
```

## 输出格式
请严格输出 JSON 数组格式，每个用例尽量简洁：

```json
[
    {{
        "name": "用例名称",
        "url": "/api/path",
        "request_method": "GET|POST|PUT|DELETE|PATCH",
        "body_type": 0-5,
        "body": {{}},
        "asserts": [
            {{
                "assert_type": "status_code",
                "expected": "200",
                "actually": ""
            }}
        ]
    }}
]
```

## 要求
1. 只生成有实际业务意义的 API（排除 health、metrics、ping 等）
2. 每个用例必须有 HTTP 状态码断言
3. 请求体参数来自 OpenAPI 的 requestBody
4. 优先为 POST/PUT 请求生成请求体
5. 用例名称控制在 15 字以内
6. 最多生成 {max_cases} 个用例
7. 只输出 JSON 数组，不要任何说明文字
"""

    # OpenAPI 分批生成 Prompt（单批）
    BATCH_GENERATE_SINGLE_TEMPLATE = """你是一个专业的 API 测试工程师。请为以下 OpenAPI 端点生成测试用例。

## OpenAPI 路径列表
{paths}

## 输出格式
请严格输出 JSON 数组格式：

```json
[
    {{
        "name": "用例名称",
        "url": "/api/path",
        "request_method": "GET|POST|PUT|DELETE|PATCH",
        "body_type": 0-5,
        "body": {{}},
        "asserts": [
            {{
                "assert_type": "status_code",
                "expected": "200",
                "actually": ""
            }}
        ]
    }}
]
```

## 要求
1. 只生成有实际业务意义的 API（排除 health、metrics、ping 等）
2. 每个用例必须有 HTTP 状态码断言
3. 请求体参数来自 OpenAPI 的 requestBody
4. 用例名称控制在 15 字以内
5. 只输出 JSON 数组，不要任何说明文字
"""

    # cURL 解析 Prompt
    CURL_PARSE_TEMPLATE = """你是一个专业的 API 测试工程师。请解析以下 cURL 命令并生成测试用例。

## cURL 命令
```bash
{curl_command}
```

## 输出格式
请严格输出 JSON 格式：

```json
{{
    "name": "用例名称",
    "url": "/api/path",
    "request_method": "GET|POST|PUT|DELETE|PATCH",
    "body_type": 0-5,
    "request_headers": {{}},
    "body": {{}},
    "asserts": [
        {{
            "assert_type": "equal|status_code",
            "expected": "200或0",
            "actually": "$.code或$.status"
        }}
    ]
}}
```

## 要求
1. 正确提取 URL、方法、请求头、请求体
2. 请求头中的 Authorization、Content-Type 要保留
3. JSON 请求体要格式化
4. 生成基础断言
"""

    def generate_case_prompt(self, api_description: str) -> str:
        """生成用例 Prompt"""
        return self.GENERATE_CASE_TEMPLATE.replace("{api_description}", api_description)

    def enhance_asserts_prompt(self, case_info: dict, response_sample: str) -> str:
        """增强断言 Prompt"""
        return self.ENHANCE_ASSERTS_TEMPLATE.replace("{case_name}", case_info.get("name", "")).replace(
            "{url}", case_info.get("url", "")).replace("{method}", case_info.get("request_method", "")).replace(
            "{body}", json.dumps(case_info.get("body", {}), ensure_ascii=False)).replace(
            "{response_sample}", response_sample)

    def batch_generate_prompt(self, openapi_spec: str, max_cases: int = 20) -> str:
        """批量生成 Prompt"""
        return self.BATCH_GENERATE_TEMPLATE.replace("{openapi_spec}", openapi_spec).replace(
            "{max_cases}", str(max_cases)
        )

    def batch_generate_single_prompt(self, paths: str) -> str:
        """单批生成 Prompt（分批处理时使用）"""
        return self.BATCH_GENERATE_SINGLE_TEMPLATE.replace("{paths}", paths)

    def parse_curl_prompt(self, curl_command: str) -> str:
        """cURL 解析 Prompt"""
        return self.CURL_PARSE_TEMPLATE.replace("{curl_command}", curl_command)
