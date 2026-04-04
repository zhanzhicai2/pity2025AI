"""
数据池 - 测试数据生成器
"""
import random
import re
from typing import Optional, Dict, Any


class ChineseNameGenerator:
    """中文姓名生成器"""

    surnames = [
        "王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
        "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
        "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
        "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
    ]

    given_names = [
        "伟", "芳", "娜", "秀", "敏", "静", "丽", "强", "磊", "军",
        "洋", "勇", "艳", "杰", "涛", "明", "超", "秀", "霞", "平",
        "刚", "桂", "英", "华", "建", "云", "海", "雪", "梅", "兰",
        "小龙", "小虎", "小丽", "小军", "小明", "小红", "小芳", "小英",
    ]

    @classmethod
    def generate(cls, gender: Optional[str] = None) -> str:
        """生成中文姓名"""
        surname = random.choice(cls.surnames)
        given_name = random.choice(cls.given_names)
        return surname + given_name


class ChinesePhoneGenerator:
    """中国手机号生成器"""

    prefixes = [
        "130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
        "150", "151", "152", "153", "155", "156", "157", "158", "159",
        "170", "171", "172", "173", "175", "176", "177", "178",
        "180", "181", "182", "183", "184", "185", "186", "187", "188", "189",
    ]

    @classmethod
    def generate(cls) -> str:
        """生成中国手机号"""
        prefix = random.choice(cls.prefixes)
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return prefix + suffix


class ChineseEmailGenerator:
    """中文邮箱生成器"""

    domains = [
        "qq.com", "163.com", "126.com", "sina.com", "sohu.com",
        "yahoo.com.cn", "gmail.com", "hotmail.com", "outlook.com",
    ]

    @classmethod
    def generate(cls, name: Optional[str] = None) -> str:
        """生成邮箱"""
        if name is None:
            name = ChineseNameGenerator.generate()

        # 移除空格
        name = name.replace(" ", "")

        # 随机选择邮箱后缀
        domain = random.choice(cls.domains)

        # 随机决定邮箱格式
        format_type = random.randint(1, 3)
        if format_type == 1:
            # 全拼 + 随机数字
            email_name = pinyin(name) + str(random.randint(10, 999))
        elif format_type == 2:
            # 首字母 + 随机数字
            email_name = ''.join([c[0] for c in name if c]) + str(random.randint(10, 999))
        else:
            # 全拼
            email_name = pinyin(name)

        return f"{email_name}@{domain}"


def pinyin(name: str) -> str:
    """简单的汉字转拼音（仅处理常用字）"""
    pinyin_map = {
        "王": "wang", "李": "li", "张": "zhang", "刘": "liu", "陈": "chen",
        "杨": "yang", "赵": "zhao", "黄": "huang", "周": "zhou", "吴": "wu",
        "徐": "xu", "孙": "sun", "胡": "hu", "朱": "zhu", "高": "gao",
        "林": "lin", "何": "he", "郭": "guo", "马": "ma", "罗": "luo",
        "伟": "wei", "芳": "fang", "娜": "na", "秀": "xiu", "敏": "min",
        "静": "jing", "丽": "li", "强": "qiang", "磊": "lei", "军": "jun",
        "洋": "yang", "勇": "yong", "艳": "yan", "杰": "jie", "涛": "tao",
        "明": "ming", "超": "chao", "霞": "xia", "平": "ping", "刚": "gang",
        "勇": "yong", "华": "hua", "建": "jian", "云": "yun", "海": "hai",
        "龙": "long", "虎": "hu", "军": "jun", "明": "ming", "红": "hong",
        "英": "ying", "梅": "mei", "兰": "lan", "雪": "xue",
    }
    result = []
    for char in name:
        result.append(pinyin_map.get(char, char))
    return ''.join(result)


class ChineseIdCardGenerator:
    """中国身份证号生成器"""

    # 省份代码（部分）
    provinces = {
        "北京": "110000", "天津": "120000", "河北": "130000", "山西": "140000",
        "内蒙古": "150000", "辽宁": "210000", "吉林": "220000", "黑龙江": "230000",
        "上海": "310000", "江苏": "320000", "浙江": "330000", "安徽": "340000",
        "福建": "350000", "江西": "360000", "山东": "370000", "河南": "410000",
        "湖北": "420000", "湖南": "430000", "广东": "440000", "广西": "450000",
        "海南": "460000", "重庆": "500000", "四川": "510000", "贵州": "520000",
        "云南": "530000", "西藏": "540000", "陕西": "610000", "甘肃": "620000",
        "青海": "630000", "宁夏": "640000", "新疆": "650000",
    }

    @classmethod
    def generate(cls, province: Optional[str] = None, birth_date: Optional[str] = None,
                 gender: Optional[str] = None) -> str:
        """生成身份证号"""
        # 随机选择省份
        if province is None:
            province = random.choice(list(cls.provinces.keys()))

        # 获取省份代码
        if province not in cls.provinces:
            province = "北京"
        code = cls.provinces[province]

        # 随机生成出生日期
        if birth_date is None:
            year = random.randint(1960, 2000)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            birth_date = f"{year:04d}{month:02d}{day:02d}"

        # 随机生成顺序码（3位）
        seq = random.randint(1, 999)

        # 奇数为男性，偶数为女性
        if gender == "male":
            seq = seq if seq % 2 == 1 else seq + 1
        elif gender == "female":
            seq = seq if seq % 2 == 0 else seq - 1

        # 计算校验码
        body = code + birth_date + f"{seq:03d}"
        check_code = cls._calculate_check_code(body)
        return body + check_code

    @staticmethod
    def _calculate_check_code(body: str) -> str:
        """计算校验码"""
        # 加权因子
        weight_factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

        total = sum(int(body[i]) * weight_factors[i] for i in range(17))
        return check_codes[total % 11]


class ChineseAddressGenerator:
    """中文地址生成器"""

    provinces = ["北京", "上海", "天津", "重庆", "河北", "山西", "辽宁", "吉林",
                 "黑龙江", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
                 "湖北", "湖南", "广东", "海南", "四川", "贵州", "云南", "陕西"]

    cities = ["市", "市", "市", "市"]  # 简化处理
    districts = ["区", "县", "市"]

    streets = [
        "人民路", "建设路", "解放路", "文化路", "胜利路", "和平路",
        "长江路", "黄河路", "北京路", "上海路", "南京路", "广州路",
    ]

    @classmethod
    def generate(cls, province: Optional[str] = None) -> str:
        """生成中文地址"""
        if province is None:
            province = random.choice(cls.provinces)

        city = province[:2] + random.choice(["市", "市", "市"]) if len(province) == 2 else province + "市"
        district = random.choice(["区", "县", "市"])
        street = random.choice(cls.streets)
        number = random.randint(1, 999)

        return f"{province}{city}{district}{street}{number}号"


class CompanyNameGenerator:
    """公司名称生成器"""

    prefixes = [
        "北京", "上海", "深圳", "广州", "杭州", "南京", "武汉", "成都",
        "西安", "苏州", "天津", "重庆", "青岛", "长沙", "郑州", "沈阳",
    ]

    names = [
        "华", "中", "国", "金", "银", "星", "云", "龙", "凤", "天",
        "海", "宇", "航", "光", "电", "力", "德", "仁", "信", "义",
    ]

    types = ["科技有限公司", "实业有限公司", "贸易有限公司", "网络科技有限公司",
             "信息科技有限公司", "文化传媒有限公司", "电子商务有限公司"]

    @classmethod
    def generate(cls, city: Optional[str] = None) -> str:
        """生成公司名称"""
        if city is None:
            city = random.choice(cls.prefixes)

        name1 = random.choice(cls.names)
        name2 = random.choice(cls.names)
        type_name = random.choice(cls.types)

        return f"{city}{name1}{name2}{type_name}"


class BankCardGenerator:
    """银行卡号生成器"""

    # 部分银行 BIN（仅示意）
    bank_bins = {
        "工商银行": "620200", "建设银行": "621700", "农业银行": "622848",
        "中国银行": "621660", "招商银行": "622609", "交通银行": "622260",
    }

    @classmethod
    def generate(cls, bank: Optional[str] = None) -> str:
        """生成银行卡号"""
        if bank is None:
            bank = random.choice(list(cls.bank_bins.keys()))

        bin_code = cls.bank_bins.get(bank, "620200")

        # 生成 12 位随机数字
        body = ''.join([str(random.randint(0, 9)) for _ in range(12)])

        # 计算 Luhn 校验码
        check_digit = cls._calculate_luhn(bin_code + body)

        return bin_code + body + str(check_digit)

    @staticmethod
    def _calculate_luhn(card_number: str) -> int:
        """计算 Luhn 校验码"""
        digits = [int(d) for d in card_number]
        # 从右往左，每位乘以 2，然后如果是偶数位则再加回去
        total = 0
        for i, d in enumerate(reversed(digits)):
            d = d * 2 if (len(digits) - i) % 2 == 0 else d
            total += d if d < 10 else d - 9
        return (10 - (total % 10)) % 10


# 工具注册表
TOOLS: Dict[str, Dict[str, Any]] = {
    "chinese_name": {
        "name": "中文姓名",
        "category": "test_data",
        "generator": ChineseNameGenerator.generate,
        "params": [
            {"name": "gender", "type": "select", "options": ["不限制", "male", "female"], "default": "不限制"}
        ]
    },
    "chinese_phone": {
        "name": "手机号",
        "category": "test_data",
        "generator": ChinesePhoneGenerator.generate,
        "params": []
    },
    "chinese_email": {
        "name": "邮箱",
        "category": "test_data",
        "generator": ChineseEmailGenerator.generate,
        "params": [
            {"name": "name", "type": "text", "label": "姓名(可选)"}
        ]
    },
    "chinese_id_card": {
        "name": "身份证号",
        "category": "test_data",
        "generator": ChineseIdCardGenerator.generate,
        "params": [
            {"name": "gender", "type": "select", "options": ["不限制", "male", "female"], "default": "不限制"}
        ]
    },
    "chinese_address": {
        "name": "中文地址",
        "category": "test_data",
        "generator": ChineseAddressGenerator.generate,
        "params": []
    },
    "company_name": {
        "name": "公司名称",
        "category": "test_data",
        "generator": CompanyNameGenerator.generate,
        "params": []
    },
    "bank_card": {
        "name": "银行卡号",
        "category": "test_data",
        "generator": BankCardGenerator.generate,
        "params": []
    },
}


def get_tool_list() -> list:
    """获取所有工具列表"""
    tools = []
    for tool_name, tool_info in TOOLS.items():
        tools.append({
            "name": tool_name,
            "display_name": tool_info["name"],
            "category": tool_info["category"],
            "params": tool_info.get("params", [])
        })
    return tools


def get_tool_categories() -> dict:
    """获取工具分类"""
    categories = {}
    for tool_name, tool_info in TOOLS.items():
        category = tool_info["category"]
        if category not in categories:
            categories[category] = {
                "name": category,
                "tools": []
            }
        categories[category]["tools"].append({
            "name": tool_name,
            "display_name": tool_info["name"],
            "params": tool_info.get("params", [])
        })
    return list(categories.values())


def generate_data(tool_name: str, params: Optional[dict] = None) -> Any:
    """生成数据"""
    if tool_name not in TOOLS:
        raise ValueError(f"未知的工具: {tool_name}")

    tool = TOOLS[tool_name]
    generator = tool["generator"]
    params = params or {}

    # 处理性别参数
    if "gender" in params:
        gender = params["gender"]
        if gender == "不限制":
            params.pop("gender", None)
        elif gender not in ("male", "female"):
            params.pop("gender", None)

    return generator(**params)
