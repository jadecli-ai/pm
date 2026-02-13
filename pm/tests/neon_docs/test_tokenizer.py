# pm/tests/neon_docs/test_tokenizer.py
"""Tests for tiktoken-based token counter."""

from lib.neon_docs.tokenizer import count_tokens


class TestTokenizer:
    def test_empty_string(self) -> None:
        assert count_tokens("") == 0

    def test_single_word(self) -> None:
        result = count_tokens("hello")
        assert result == 1

    def test_sentence(self) -> None:
        result = count_tokens("The quick brown fox jumps over the lazy dog.")
        assert 8 <= result <= 12

    def test_accuracy_vs_naive(self) -> None:
        text = "This is a test of the token counting accuracy."
        actual = count_tokens(text)
        assert actual > 0

    def test_code_tokens(self) -> None:
        code = "def hello_world():\n    print('hello')\n"
        result = count_tokens(code)
        assert result > 5
