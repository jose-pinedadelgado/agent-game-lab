"""Unit tests for output parsing."""

import pytest

from pdbench.core.parse import OutputParser, ParseError, RetryParser
from pdbench.core.types import Action


class TestOutputParser:
    """Tests for OutputParser."""

    def test_parse_c(self) -> None:
        """Test parsing 'C'."""
        parser = OutputParser()
        assert parser.parse("C") == Action.COOPERATE

    def test_parse_d(self) -> None:
        """Test parsing 'D'."""
        parser = OutputParser()
        assert parser.parse("D") == Action.DEFECT

    def test_case_insensitive(self) -> None:
        """Test case-insensitive parsing."""
        parser = OutputParser()
        assert parser.parse("c") == Action.COOPERATE
        assert parser.parse("d") == Action.DEFECT

    def test_strips_whitespace(self) -> None:
        """Test whitespace stripping."""
        parser = OutputParser()
        assert parser.parse("  C  ") == Action.COOPERATE
        assert parser.parse("\nD\n") == Action.DEFECT
        assert parser.parse("\t C \t") == Action.COOPERATE

    def test_invalid_output_raises(self) -> None:
        """Test that invalid outputs raise ParseError."""
        parser = OutputParser()

        with pytest.raises(ParseError):
            parser.parse("X")

        with pytest.raises(ParseError):
            parser.parse("Cooperate")

        with pytest.raises(ParseError):
            parser.parse("CD")

        with pytest.raises(ParseError):
            parser.parse("")

    def test_try_parse_success(self) -> None:
        """Test try_parse on valid input."""
        parser = OutputParser()
        attempt = parser.try_parse("C")

        assert attempt.success
        assert attempt.parsed_action == Action.COOPERATE
        assert attempt.error_message is None

    def test_try_parse_failure(self) -> None:
        """Test try_parse on invalid input."""
        parser = OutputParser()
        attempt = parser.try_parse("invalid")

        assert not attempt.success
        assert attempt.parsed_action is None
        assert attempt.error_message is not None


class TestRetryParser:
    """Tests for RetryParser."""

    def test_success_no_retry(self) -> None:
        """Test successful parse without retry."""
        parser = RetryParser(max_retries=2)
        action = parser.parse_with_retry("C")

        assert action == Action.COOPERATE
        assert len(parser.attempts) == 1
        assert parser.attempts[0].success

    def test_retry_on_failure(self) -> None:
        """Test retry after initial failure."""
        parser = RetryParser(max_retries=2)

        call_count = 0

        def retry_callback(correction: str) -> str:
            nonlocal call_count
            call_count += 1
            return "D"  # Return valid on retry

        action = parser.parse_with_retry("invalid", retry_callback)

        assert action == Action.DEFECT
        assert len(parser.attempts) == 2
        assert not parser.attempts[0].success
        assert parser.attempts[1].success
        assert call_count == 1

    def test_max_retries_exhausted(self) -> None:
        """Test ParseError when max retries exhausted."""
        parser = RetryParser(max_retries=2)

        def retry_callback(correction: str) -> str:
            return "still invalid"

        with pytest.raises(ParseError):
            parser.parse_with_retry("invalid", retry_callback)

        # Initial + 2 retries = 3 attempts
        assert len(parser.attempts) == 3

    def test_no_retry_callback(self) -> None:
        """Test failure without retry callback."""
        parser = RetryParser(max_retries=2)

        with pytest.raises(ParseError):
            parser.parse_with_retry("invalid", retry_callback=None)

        # Only initial attempt
        assert len(parser.attempts) == 1

    def test_correction_prompt_in_callback(self) -> None:
        """Test that correction prompt is passed to callback."""
        parser = RetryParser(max_retries=2)
        received_prompt = None

        def retry_callback(correction: str) -> str:
            nonlocal received_prompt
            received_prompt = correction
            return "C"

        parser.parse_with_retry("invalid", retry_callback)

        assert received_prompt is not None
        assert "C or D" in received_prompt
