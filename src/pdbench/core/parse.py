"""Strict output parsing with retry logic."""

from __future__ import annotations

from dataclasses import dataclass

from pdbench.core.types import Action


class ParseError(Exception):
    """Raised when output cannot be parsed to a valid action."""

    pass


@dataclass
class ParseAttempt:
    """Record of a parse attempt."""

    raw_output: str
    parsed_action: Action | None
    success: bool
    error_message: str | None = None


class OutputParser:
    """Parses agent outputs to valid actions."""

    VALID_ACTIONS = {"C", "D"}

    def parse(self, raw_output: str) -> Action:
        """Parse raw output to an Action.

        Accepts:
        - "C" or "D" (case-insensitive)
        - Leading/trailing whitespace is stripped

        Raises ParseError if output is invalid.
        """
        cleaned = raw_output.strip().upper()

        if cleaned in self.VALID_ACTIONS:
            return Action(cleaned)

        raise ParseError(
            f"Invalid output: '{raw_output}'. Expected 'C' or 'D'."
        )

    def try_parse(self, raw_output: str) -> ParseAttempt:
        """Try to parse, returning a ParseAttempt with success/failure info."""
        try:
            action = self.parse(raw_output)
            return ParseAttempt(
                raw_output=raw_output,
                parsed_action=action,
                success=True,
            )
        except ParseError as e:
            return ParseAttempt(
                raw_output=raw_output,
                parsed_action=None,
                success=False,
                error_message=str(e),
            )


class RetryParser:
    """Parser with retry logic for LLM outputs."""

    CORRECTION_PROMPT = (
        "Your previous response was invalid. "
        "Please respond with ONLY a single character: C or D. "
        "No explanation, no punctuation, just C or D."
    )

    def __init__(self, max_retries: int = 2) -> None:
        """Initialize with max retry count."""
        self._max_retries = max_retries
        self._parser = OutputParser()
        self._attempts: list[ParseAttempt] = []

    @property
    def attempts(self) -> list[ParseAttempt]:
        """Get all parse attempts from the last parse_with_retry call."""
        return self._attempts

    @property
    def max_retries(self) -> int:
        """Get max retries."""
        return self._max_retries

    def parse_with_retry(
        self,
        initial_output: str,
        retry_callback: callable | None = None,  # Called with correction prompt, returns new output
    ) -> Action:
        """Parse with retries.

        Args:
            initial_output: The first output to parse.
            retry_callback: Function that takes a correction prompt and returns a new output.
                           If None, no retries are attempted.

        Returns:
            The parsed Action.

        Raises:
            ParseError if all attempts fail.
        """
        self._attempts = []

        # First attempt
        attempt = self._parser.try_parse(initial_output)
        self._attempts.append(attempt)

        if attempt.success:
            return attempt.parsed_action  # type: ignore

        # Retry loop
        for _ in range(self._max_retries):
            if retry_callback is None:
                break

            new_output = retry_callback(self.CORRECTION_PROMPT)
            attempt = self._parser.try_parse(new_output)
            self._attempts.append(attempt)

            if attempt.success:
                return attempt.parsed_action  # type: ignore

        # All attempts failed
        raise ParseError(
            f"Failed to parse after {len(self._attempts)} attempts. "
            f"Last output: '{self._attempts[-1].raw_output}'"
        )
