import pytest
import json
from src.chain import parse_json_spec, slugify

def test_parse_json_spec_valid():
    text = '{"key": "value", "number": 42}'
    result = parse_json_spec(text)
    assert result == {"key": "value", "number": 42}

def test_parse_json_spec_with_extra_text():
    text = 'Some text before {"key": "value"} and after'
    result = parse_json_spec(text)
    assert result == {"key": "value"}

def test_parse_json_spec_invalid():
    with pytest.raises(ValueError, match="Не удалось извлечь JSON из ответа модели."):
        parse_json_spec("not a json")

def test_slugify_basic():
    assert slugify("Hello World") == "hello_world"
    assert slugify("  leading and trailing  ") == "leading_and_trailing"
    assert slugify("Special chars!@#") == "special_chars"
    assert slugify("Multiple   spaces") == "multiple_spaces"
    assert slugify("123 numbers") == "123_numbers"
    assert slugify("") == "article"
    assert slugify("___") == "article"  # после замены на подчеркивания и обрезки останется пусто