# LLM Guardrail Fuzzer

A fuzzing tool for systematically testing LLM safety guardrails. Inspired by traditional security fuzzing techniques adapted for language model testing.

## Concept

In traditional pentesting, fuzzing means sending large volumes of malformed or unexpected inputs to find crashes and vulnerabilities. This tool applies the same principle to LLM guardrails — generating and testing thousands of prompt variations to find where safety filters break down.

## Fuzzing Strategies

### 1. Synonym Substitution
Replaces known blocked words with synonyms, slang, misspellings, or leetspeak to test if content filters rely on keyword matching.

### 2. Encoding Attacks
Tests prompts using various encoding schemes: base64, ROT13, pig latin, reversed text, character substitution.

### 3. Language Mixing
Combines multiple languages in a single prompt to test if safety filters work across languages.

### 4. Structural Fuzzing
Varies prompt structure: questions vs statements, first person vs third person, hypothetical framing, academic framing.

### 5. Context Window Manipulation
Tests how safety behavior changes with very long prompts, nested instructions, or prompts that push against context limits.

## Usage

```bash
pip install -r requirements.txt

# Run basic fuzz test
python src/fuzzer.py --target-model gpt-4o-mini --strategy synonym --category harmful_content

# Run all strategies against a model
python src/fuzzer.py --target-model gpt-4o-mini --strategy all --output results/fuzz_report.json

# Generate fuzz corpus for a specific risk category
python src/corpus_generator.py --category emotional_manipulation --count 100
```

## Output

```json
{
  "total_prompts_tested": 500,
  "guardrail_bypasses": 12,
  "bypass_rate": "2.4%",
  "bypasses_by_strategy": {
    "synonym_substitution": 5,
    "encoding": 3,
    "structural": 4
  },
  "most_vulnerable_category": "emotional_manipulation"
}
```

## Adapting from Traditional Pentesting

| Traditional Fuzzing | LLM Guardrail Fuzzing |
|---|---|
| Malformed HTTP requests | Malformed prompts |
| SQL injection payloads | Prompt injection payloads |
| Buffer overflow strings | Context window overflow |
| Character encoding attacks | Language/encoding bypass |
| Input validation bypass | Content filter bypass |

## Ethics

This tool is designed for authorized safety testing only. Use it to find and fix vulnerabilities in your own AI products, not to exploit others.
