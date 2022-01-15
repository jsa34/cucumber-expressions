import re

import pytest

from Cucumber.CucumberExpressions.cucumber_expression import CucumberExpression
from Cucumber.CucumberExpressions.parameter_type import ParameterType
from Cucumber.CucumberExpressions.parameter_type_registry import ParameterTypeRegistry
from Cucumber.CucumberExpressions.regular_expression import RegularExpression
from Cucumber.CucumberExpressions.exceptions.errors import CucumberExpressionError


class Color:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Color) and other.name == self.name


class CssColor:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, CssColor) and other.name == self.name


class Coordinate:
    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return (
            isinstance(other, Coordinate)
            and other.x == self.x
            and self.y == other.y
            and self.z == other.z
        )


class TestCustomParameterType:
    _parameter_type_registry = ParameterTypeRegistry()
    _parameter_type_registry.define_parameter_type(
        ParameterType(
            "color",
            re.compile("red|blue|yellow"),
            Color,
            lambda s: Color(s),
            True,
            False,
        )
    )

    def test_throws_exception_for_illegal_character_in_parameter_name(self):
        with pytest.raises(CucumberExpressionError):
            ParameterType("[string]", re.compile(r".*"), str, lambda s: s, True, False)

    def test_matches_parameters_with_custom_parameter_type(self):
        expression = CucumberExpression(
            "I have a {color} ball", self._parameter_type_registry
        )
        transformed_argument_value = expression.match("I have a red ball")[0]
        assert transformed_argument_value.value == Color("red")

    def test_matches_parameters_with_multiple_capture_groups(self):
        self._parameter_type_registry.define_parameter_type(
            ParameterType(
                "coordinate",
                r"(\d+),\s*(\d+),\s*(\d+)",
                Coordinate,
                lambda x, y, z: Coordinate(int(x), int(y), int(z)),
                True,
                False,
            )
        )

        expression = CucumberExpression(
            "A {int} thick line from {coordinate} to {coordinate}",
            self._parameter_type_registry,
        )
        args = expression.match("A 5 thick line from 10,20,30 to 40,50,60")

        thick = args[0].value
        assert thick == 5

        _from = args[1].value
        assert _from == Coordinate(10, 20, 30)

        to = args[2].value
        assert to == Coordinate(40, 50, 60)

    def test_matches_parameters_with_custom_parameter_type_using_optional_capture_group(
        self,
    ):
        parameter_type_registry = ParameterTypeRegistry()
        parameter_type_registry.define_parameter_type(
            ParameterType(
                "color",
                [
                    re.compile(r"red|blue|yellow"),
                    re.compile(r"(?:dark|light) (?:red|blue|yellow)"),
                ],
                Color,
                lambda s: Color(s),
                True,
                False,
            )
        )
        expression = CucumberExpression(
            "I have a {color} ball", parameter_type_registry
        )
        transformed_argument_value = expression.match("I have a dark red ball")[0].value
        assert transformed_argument_value == Color("dark red")

    def test_defers_transformation_until_queried_from_argument(self):
        class TestException(Exception):
            pass

        with pytest.raises(TestException) as excinfo:
            self._parameter_type_registry.define_parameter_type(
                ParameterType(
                    "throwing",
                    re.compile("bad"),
                    CssColor,
                    lambda s: (_ for _ in ()).throw(
                        TestException(f"Can't transform [{s}]")
                    ),
                    True,
                    False,
                )
            )
            expression = CucumberExpression(
                "I have a {throwing} parameter", self._parameter_type_registry
            )
            args = expression.match("I have a bad parameter")
            args[0].value()

        assert excinfo.value.args[0] == "Can't transform [bad]"

    def test_conflicting_parameter_type_is_detected_for_type_name(self):
        with pytest.raises(CucumberExpressionError) as excinfo:
            assert self._parameter_type_registry.define_parameter_type(
                ParameterType(
                    "color",
                    re.compile(r".*"),
                    CssColor,
                    lambda s: CssColor(s),
                    True,
                    False,
                )
            )

        assert excinfo.value.args[0] == "There is already a parameter with name color"

    def test_conflicting_parameter_type_is_not_detected_for_regexp(self):
        self._parameter_type_registry.define_parameter_type(
            ParameterType(
                "css-color",
                re.compile(r"red|blue|yellow"),
                CssColor,
                lambda s: CssColor(s),
                True,
                False,
            )
        )

        css_color = CucumberExpression(
            "I have a {css-color} ball", self._parameter_type_registry
        )
        css_color_value = css_color.match("I have a blue ball")[0].value
        assert css_color_value == CssColor("blue")

        color = CucumberExpression(
            "I have a {color} ball", self._parameter_type_registry
        )
        color_value = color.match("I have a blue ball")[0].value
        assert color_value == Color("blue")

    def test_regular_expression_matches_arguments_with_custom_parameter_type_without_name(
        self,
    ):
        parameter_type_registry = ParameterTypeRegistry()
        parameter_type_registry.define_parameter_type(
            ParameterType(
                None,
                re.compile(r"red|blue|yellow"),
                Color,
                lambda s: Color(s),
                True,
                False,
            )
        )
        expression = RegularExpression(
            r"I have a (red|blue|yellow) ball", parameter_type_registry
        )
        transformed_argument_value = expression.match("I have a red ball")[0].value
        assert transformed_argument_value == Color("red")
