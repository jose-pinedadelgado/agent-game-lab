"""OpenAI provider adapter."""

from __future__ import annotations

import os

from openai import OpenAI


# TODO: Add LiteLLM provider adapter (litellm.py) for multi-provider support
#       via a single dependency. LiteLLM wraps OpenAI, Anthropic, Cohere, etc.


class OpenAIProvider:
    """Provider that calls the OpenAI Chat Completions API."""

    def __init__(self, model: str = "gpt-4.1-mini", api_key: str | None = None) -> None:
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it in your .env file or environment."
            )
        self._client = OpenAI(api_key=key)
        self._model = model

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
