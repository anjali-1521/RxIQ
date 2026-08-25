# AI Insight Narrator — Model Selection Notes

`scripts/04_ai_insight_narrator.py` computes RxIQ's headline KPIs directly
from `rxiq_tableau_flat.csv` with pandas, then passes those computed facts
— as a JSON block, not the raw dataset — to a local LLM (Ollama) to draft a
ZS-style one-page recommendation memo. Everything runs offline; no sales or
rep data leaves the machine.

## Why ground the prompt instead of letting the model see raw rows

LLMs are unreliable at arithmetic over large tables and prone to inventing
plausible-looking numbers. Doing the math in pandas first and having the
LLM only narrate pre-verified figures removes that failure mode by
construction — the model literally never sees a number it didn't receive,
so it can't misstate one that wasn't in its input.

## But grounding isn't the whole story: model size still matters

The same prompt, with identical grounding facts, was run against two local
models on this 8GB machine.

**`llama3.2:1b`** (1.3GB) — despite the facts explicitly stating the dataset
covers Poland and Germany, the output invented a "US territory" that
appears nowhere in the data, misread the disproven coverage-gap hypothesis
as the actual finding, and reported product-class percentages as "% of
total reps" instead of sales:

> "We investigated whether Jimmy Grey's performance is significantly better
> than Alan Ray's in coverage of all 749 cities across the **US territory**."
>
> "...Analgesics accounts for 20.1% of **total reps**..."

**`llama3.2:3b`** (2.0GB) — same prompt, same facts, correctly reframed the
disproven hypothesis, cited every number exactly as given, invented nothing:

> "Our analysis tested the territory-coverage-gap hypothesis... our findings
> suggest that this hypothesis is incorrect, as our data indicates that
> every representative covers all 749 cities in the territory. The real
> finding is a per-rep efficiency gap of 16.4% between our top-performing
> representative, Jimmy Grey, and our bottom-performing representative,
> Alan Ray."

`llama3.2:3b` is the default in the script for this reason.

## The actual takeaway

Fact-grounding narrows *what* an LLM can say wrong (it can't cite a number
it was never given), but it doesn't guarantee faithful *use* of what it was
given — a small enough model will still misread or invent context around
correct facts. In a client-facing analytics workflow this is exactly why
AI-generated output is treated as a first draft requiring human review, not
a final deliverable — which is also why the generated memo
(`reports/ai_generated_memo.md`) is labeled as a draft, not a final memo, in
its own header.
