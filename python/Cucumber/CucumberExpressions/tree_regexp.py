import re

from Cucumber.CucumberExpressions.ast import EscapeCharacters
from Cucumber.CucumberExpressions.group_builder import GroupBuilder


class TreeRegexp:
    def __init__(self, regexp):
        self.regexp = regexp
        self._group_builder = None
        if not self._group_builder:
            self._group_builder = self.create_group_builder(re.compile(self.regexp))

    def match(self, string: str):
        matches = re.search(self.regexp, string)
        if not matches:
            return None
        group_indices = range(0, len(matches.groups()) + 1)
        return self.group_builder.build(matches, iter(group_indices))

    def create_group_builder(self, regexp):
        source = regexp.pattern
        stack: list[GroupBuilder] = [GroupBuilder()]
        group_start_stack = []
        escaping: bool = False
        char_class: bool = False
        for index, char in enumerate(source):
            if char == "[" and not escaping:
                char_class = True
            elif char == "]" and not escaping:
                char_class = False
            elif char == "(" and not escaping and not char_class:
                group_start_stack.append(index)
                group_builder = GroupBuilder()
                non_capturing = self.is_non_capturing(source, index)
                if non_capturing:
                    group_builder.capturing = False
                stack.append(group_builder)
            elif char == ")" and not escaping and not char_class:
                gb = stack.pop()
                if not gb:
                    raise Exception("Empty stack!")
                group_start = group_start_stack.pop()
                group_start = group_start if group_start else 0
                if gb.capturing:
                    gb.source = source[(group_start + 1) : index]
                    stack[len(stack) - 1].add(gb)
                else:
                    gb.move_children_to(stack[len(stack) - 1])
                gb.end_index = index
            escaping = (char == EscapeCharacters.ESCAPE_CHARACTER.value) and (
                not escaping
            )
        return stack.pop()

    @staticmethod
    def is_non_capturing(source, index):
        # Regex is valid. Bounds check not required.
        if source[index + 1] != "?":
            # (X)
            return False
        if source[index + 2] != "<":
            # (?:X)
            # (?idmsuxU-idmsuxU)
            # (?idmsux-idmsux:X)
            # (?=X)
            # (?!X)
            # (?>X)
            return True
        # (?<=X) or (?<!X) else (?<name>X)
        return source[index + 3] in ["=", "!"]

    @property
    def group_builder(self):
        return self._group_builder
