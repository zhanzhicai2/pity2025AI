from app.crud import Mapper, ModelWrapper, connect
from app.models.mock_rule import MockRule


@ModelWrapper(MockRule)
class MockRuleDao(Mapper):
    pass
