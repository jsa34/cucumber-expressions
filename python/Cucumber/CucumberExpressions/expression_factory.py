from typing import Union, Pattern

from Cucumber.CucumberExpressions.cucumber_expression import CucumberExpression
from Cucumber.CucumberExpressions.regular_expression import RegularExpression
from Cucumber.CucumberExpressions.exceptions.errors import CucumberExpressionError


class ExpressionFactory:
    def __init__(self, parameter_type_registry):
        self.parameter_type_registry = parameter_type_registry

    def create_expression(self, string_or_regexp: Union[str, Pattern]):
        if isinstance(string_or_regexp, str):
            return CucumberExpression(string_or_regexp, self.parameter_type_registry)
        elif isinstance(string_or_regexp, Pattern):
            return RegularExpression(string_or_regexp, self.parameter_type_registry)
        else:
            raise CucumberExpressionError(
                f"Can't create an expression from: {str(string_or_regexp)}"
            )
