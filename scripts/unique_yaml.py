#!/usr/bin/env python3
"""One YAML loader for workflow sensors.

Import ``load_yaml`` from this module. Do not hand-parse mappings.

The loader is a PyYAML ``SafeLoader``. It refuses:

- a repeated key (the document has no value for that key)
- an anchor (``&name``) or an alias (``*name``)
- a merge key (``<<``)
- an explicit key (``?``), including ``? if`` and a sequence or mapping key

A quoted key (``"if":``, ``'run':``) is an ordinary scalar key. PyYAML emits a
zero-width ``KeyToken`` for ``key:`` and a one-character ``KeyToken`` for ``?``.
That span is how an explicit key is told apart from a plain key.
"""
from __future__ import annotations

from yaml import YAMLError
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.events import AliasEvent
from yaml.nodes import MappingNode, ScalarNode
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import Resolver
from yaml.scanner import Scanner
from yaml.tokens import FlowEntryToken, KeyToken


class UniqueYamlError(Exception):
    """The document used a YAML feature this loader refuses."""

    def __init__(self, kind: str, detail: str = "") -> None:
        self.kind = kind
        self.detail = detail
        super().__init__(f"{kind}: {detail}" if detail else kind)


def _explicit_key(token: object) -> bool:
    return (
        isinstance(token, KeyToken)
        and token.start_mark.index != token.end_mark.index
    )


class _Parser(Parser):
    def _reject_explicit_key(self) -> None:
        """Refuse a ``?`` key. A plain ``key:`` token has an empty span."""
        self.peek_token()
        looked = 0
        while looked < 3:
            if looked >= len(self.tokens):
                if self.done:
                    return
                if not self.need_more_tokens():
                    before = len(self.tokens)
                    try:
                        self.fetch_more_tokens()
                    except YAMLError:
                        return
                    if len(self.tokens) == before:
                        return
                else:
                    self.fetch_more_tokens()
                if looked >= len(self.tokens):
                    return
            token = self.tokens[looked]
            if isinstance(token, FlowEntryToken):
                looked += 1
                continue
            if _explicit_key(token):
                raise UniqueYamlError("complex")
            return

    def parse_block_mapping_key(self):
        self._reject_explicit_key()
        return Parser.parse_block_mapping_key(self)

    def parse_flow_mapping_key(self, first=False):
        self._reject_explicit_key()
        return Parser.parse_flow_mapping_key(self, first=first)


class _Composer(Composer):
    def compose_node(self, parent, index):
        if self.check_event(AliasEvent):
            raise UniqueYamlError("alias")
        event = self.peek_event()
        if event is not None and getattr(event, "anchor", None):
            raise UniqueYamlError("anchor")
        return Composer.compose_node(self, parent, index)


class _Constructor(SafeConstructor):
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, MappingNode):
            raise UniqueYamlError("mapping")
        mapping = {}
        for key_node, value_node in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                raise UniqueYamlError("merge")
            if not isinstance(key_node, ScalarNode):
                raise UniqueYamlError("complex", "non-scalar")
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError:
                raise UniqueYamlError("complex", "unhashable") from None
            if key in mapping:
                raise UniqueYamlError("duplicate", repr(key))
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


class UniqueLoader(Reader, Scanner, _Parser, _Composer, _Constructor, Resolver):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        _Parser.__init__(self)
        _Composer.__init__(self)
        _Constructor.__init__(self)
        Resolver.__init__(self)


def load_yaml(text: str):
    """Load one YAML document.

    Raises ``UniqueYamlError`` with ``kind`` of ``duplicate``, ``anchor``,
    ``alias``, ``merge``, ``complex``, or ``syntax``.
    """
    loader = UniqueLoader(text)
    try:
        try:
            return loader.get_single_data()
        except UniqueYamlError:
            raise
        except YAMLError as exc:
            raise UniqueYamlError("syntax", str(exc)) from exc
    finally:
        loader.dispose()
