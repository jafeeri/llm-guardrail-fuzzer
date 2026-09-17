"""providers.py -- provider-agnostic LLM chat, zero dependencies (stdlib urllib).

One call, four backends, chosen by the LLM_PROVIDER env var:
  * mock      (default) -- deterministic canned replies; runs offline, free, no key
  * openai    -- api.openai.com or any OpenAI-compatible endpoint
  * anthropic -- api.anthropic.com /v1/messages
  * ollama    -- local models (http://localhost:11434), no key needed

Env vars:
  LLM_PROVIDER   mock | openai | anthropic | ollama         (default: mock)
  LLM_BASE_URL   override the endpoint base (e.g. a proxy / Groq / Together)
  LLM_API_KEY    the key; falls back to OPENAI_API_KEY / ANTHROPIC_API_KEY

Returns the assistant text as a string. Raises ProviderError on failure.
"""

import json
import os
import urllib.error
import urllib.request

DEFAULTS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "ollama": "http://localhost:11434/v1",
}


class ProviderError(Exception):
    """Any failure talking to a model backend."""


def _post(url, headers, payload, timeout):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _mock_reply(messages):
    """Deterministic offline reply. Shaped to whatever the caller asked for so the
    real parsing code paths still run. Clearly a stub -- never a real model."""
    blob = " ".join(m.get("content", "") for m in messages).lower()
    if '"bypassed"' in blob or "safety classifier" in blob:
        return ('{"bypassed": false, "inappropriate_content": false, '
                '"appropriate_refusal": true, "confidence": "HIGH", '
                '"notes": "mock: target refused"}')
    # default: a safe refusal, so a mock fuzz run shows 0% bypass (honest stub)
    return "I'm sorry, but I can't help with that. Let's talk about something else."


def call_chat(messages, model="", max_tokens=500, temperature=0.7, timeout=60):
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "mock":
        return _mock_reply(messages)

    base = os.getenv("LLM_BASE_URL", DEFAULTS.get(provider, DEFAULTS["openai"])).rstrip("/")
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or "x"
    try:
        if provider == "anthropic":
            sys = " ".join(m["content"] for m in messages if m["role"] == "system")
            chat = [m for m in messages if m["role"] != "system"]
            body = {"model": model or "claude-sonnet-4-6", "max_tokens": max_tokens,
                    "temperature": temperature, "messages": chat}
            if sys:
                body["system"] = sys
            resp = _post(base + "/messages", {"x-api-key": key,
                         "anthropic-version": "2023-06-01", "content-type": "application/json"},
                         body, timeout)
            return "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text").strip()
        # openai + ollama share the chat-completions shape
        body = {"model": model or "gpt-4o-mini", "max_tokens": max_tokens,
                "temperature": temperature, "messages": messages}
        resp = _post(base + "/chat/completions",
                     {"authorization": f"Bearer {key}", "content-type": "application/json"},
                     body, timeout)
        return (resp["choices"][0]["message"].get("content") or "").strip()
    except urllib.error.HTTPError as e:
        raise ProviderError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
    except urllib.error.URLError as e:
        raise ProviderError(f"connection error: {e.reason}")
    except (KeyError, IndexError, ValueError, TypeError) as e:
        raise ProviderError(f"unexpected response shape: {type(e).__name__}: {e}")
