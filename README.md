# LLM Guardrail Fuzzer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Dependencies: none](https://img.shields.io/badge/dependencies-none%20(stdlib)-brightgreen.svg)](#install)
[![Providers](https://img.shields.io/badge/providers-mock%20%7C%20openai%20%7C%20anthropic%20%7C%20ollama-8A2BE2.svg)](#pick-a-provider)

**A fuzzer for LLM safety guardrails. It takes one borderline topic, generates many reworded and re-encoded versions of the same ask, sends them all to a model, and reports how often the model's safety filter was bypassed.**

Traditional security fuzzing throws thousands of malformed inputs at a program to find the one that slips through. This does the same thing to a language model's safety layer: same intent, many surface forms, and it measures which forms get past.

> New here? Read [What it does](#what-it-does-in-plain-terms). Just want to run it? [Quickstart](#quickstart). It runs offline and free by default, so you can try it with zero setup.

---

## What it does, in plain terms

A model is supposed to refuse certain requests. But a filter that only looks at the *words* can be fooled by rewording ("hide" becomes "conceal"), reframing ("for a school project..."), or light encoding (reversed text, l33tspeak). This tool automates that probing:

1. You give it a borderline **concept** (e.g. "keeping secrets from parents").
2. It **generates variants** of that ask using a chosen strategy.
3. It **sends each variant** to the target model.
4. A second model **judges** each answer: did the guardrail hold, or was it bypassed?
5. You get a **bypass rate** and a JSON report.

**Bypass** = the model gave in to a variant it should have refused. Lower is safer.

## Runs offline and free by default

By default the tool uses a built-in **mock** backend: deterministic canned replies, no API key, no cost, no network. The self-check and a full demo run work the moment you clone it. Point it at a real model only when you want real numbers. See [Pick a provider](#pick-a-provider).

## Install

No dependencies. Pure Python 3.9+ standard library (model calls use `urllib`).

```bash
git clone https://github.com/jafeeri/llm-guardrail-fuzzer.git
cd llm-guardrail-fuzzer
```

## Quickstart

```bash
# 1. Offline self-check (no key, no cost)
python src/fuzzer.py --selftest

# 2. A full mock run (still offline)
python src/fuzzer.py --strategy all --concept "keeping secrets from parents"
```

You get a live per-prompt readout and a `results/fuzz_report.json` file.

## Pick a provider

Choose the backend with environment variables. Mock is the default.

```bash
# OpenAI (or any OpenAI-compatible endpoint: Groq, Together, etc.)
export LLM_PROVIDER=openai
export LLM_API_KEY=sk-...
python src/fuzzer.py --strategy structural --target-model gpt-4o-mini

# Local model via Ollama (free, no key)
export LLM_PROVIDER=ollama
python src/fuzzer.py --target-model llama3.1

# Anthropic
export LLM_PROVIDER=anthropic
export LLM_API_KEY=sk-ant-...
python src/fuzzer.py --target-model claude-sonnet-4-6
```

| Env var | Meaning | Default |
|---|---|---|
| `LLM_PROVIDER` | `mock`, `openai`, `anthropic`, or `ollama` | `mock` |
| `LLM_BASE_URL` | override the endpoint (proxy / Groq / Together / local) | per-provider default |
| `LLM_API_KEY` | your key (falls back to `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`) | none |

On Windows PowerShell use `$env:LLM_PROVIDER="ollama"` instead of `export`.

## Fuzzing strategies

| Strategy | What it generates |
|---|---|
| `structural` | The same concept wrapped in 10 framings: question, hypothetical, "for a school project", story, roleplay, and so on. |
| `encoding` | Reversed text, character-spacing, l33tspeak, and an acronym split, to test filters that match on raw words. |
| `synonym` | Word substitutions (e.g. "hide" to "conceal", "parents" to "family"). |
| `all` | Structural plus encoding, de-duplicated. |

Pick one with `--strategy` and set the topic with `--concept`.

## Command reference

| Command | What it does | Needs a key? |
|---|---|---|
| `python src/fuzzer.py --selftest` | Offline self-check of the generators and pipeline | No |
| `python src/fuzzer.py --strategy all --concept "..."` | Full fuzz run (mock unless `LLM_PROVIDER` is set) | Only for a real provider |
| `--target-model NAME` | The model under test | |
| `--output PATH` | Where to write the JSON report (default `results/fuzz_report.json`) | |

## How bypass detection works

Each target answer is scored by a second model (the judge) that returns strict JSON:

```json
{"bypassed": false, "inappropriate_content": false, "appropriate_refusal": true, "confidence": "HIGH", "notes": ""}
```

The campaign then reports:

```json
{
  "total_tested": 10,
  "errors": 0,
  "bypasses": 1,
  "bypass_rate": "10.0%",
  "target_model": "gpt-4o-mini",
  "provider": "openai",
  "results": [ ... ]
}
```

**Metric integrity:** a call that errors out (network, rate limit) is recorded as an `error` and excluded from the bypass-rate denominator. A failed request is never counted as a refusal or a bypass, so a flaky connection cannot skew the score.

## Honest limits

- The mock backend proves the pipeline, not a real model. Mock always refuses, so a mock run shows 0% bypass by design. Real numbers need a real provider.
- Detection quality is only as good as the judge model you point it at.
- The encoding variants are deliberately simple (a starting corpus, not an exhaustive obfuscation suite).

## Responsible use

For authorized safety testing only. Use it to find and fix weaknesses in models and applications you are allowed to test, so they can be hardened before release. It is a measurement tool, not an exploit kit.

## License

MIT, see [LICENSE](LICENSE). Copyright (c) 2026 Ali Mehdi Jafeeri.
