"""
RxIQ — AI Insight Narrator (Step 7 support)

Computes the project's headline KPIs directly from the cleaned data with
pandas, then hands those computed facts — not the raw dataset — to a local
LLM (Ollama, llama3.2:3b) to draft a ZS-style one-page executive narrative.

Model choice is deliberate, not default: llama3.2:1b was tried first and,
despite receiving the exact same grounded facts, fabricated a "US territory"
that does not exist anywhere in this dataset (it's Poland/Germany only) and
misattributed product-class percentages to "% of total reps" instead of
sales. llama3.2:3b, given the identical prompt, cited every figure correctly
with no invented entities. See reports/ai_narrator_notes.md for the
side-by-side. The lesson: grounding a prompt in verified facts reduces
hallucination risk but does not eliminate it — model capability still
matters, and output review remains necessary regardless of model size.

Why ground the prompt in pre-computed facts instead of letting the LLM see
raw rows: LLMs are unreliable at arithmetic over large tables and prone to
inventing plausible-looking numbers. Doing the math in pandas and having the
LLM only narrate verified figures removes that failure mode entirely — the
output can't misstate a number that was never in its input. That tradeoff
(narrative fluency from the LLM, factual correctness from code) is the
actual point being demonstrated here, not the model's math ability.

Also runs fully offline against a local model, so no sales/rep data ever
leaves the machine — a real constraint in pharma analytics, not a
hypothetical one.

Usage:
    python3 scripts/04_ai_insight_narrator.py
Requires:
    Ollama running locally with `llama3.2:3b` pulled (ollama pull llama3.2:3b)
Output:
    reports/ai_generated_memo.md
"""

import json
import urllib.request
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLAT_CSV = ROOT / "data" / "processed" / "rxiq_tableau_flat.csv"
OUT_PATH = ROOT / "reports" / "ai_generated_memo.md"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


def compute_facts(df: pd.DataFrame) -> dict:
    total_sales = df["sales"].sum()
    date_min, date_max = df["date"].min(), df["date"].max()

    country_sales = df.groupby("country")["sales"].sum().sort_values(ascending=False)
    country_pct = (country_sales / country_sales.sum() * 100).round(1)

    rep_eff = df.groupby("sales_rep")["sales_per_city"].mean().sort_values(ascending=False)
    top_rep, bottom_rep = rep_eff.index[0], rep_eff.index[-1]
    top_val, bottom_val = rep_eff.iloc[0], rep_eff.iloc[-1]
    gap_pct = (top_val / bottom_val - 1) * 100

    cities_per_rep = df.groupby("sales_rep")["city"].nunique()
    all_reps_full_coverage = cities_per_rep.nunique() == 1
    total_cities = df["city"].nunique()

    class_sales = df.groupby("product_class")["sales"].sum().sort_values(ascending=False)
    class_pct = (class_sales / class_sales.sum() * 100).round(1)
    top_class, bottom_class = class_pct.index[0], class_pct.index[-1]

    team_sales = df.groupby("sales_team")["sales"].sum().sort_values(ascending=False)

    return {
        "total_sales_usd": round(total_sales),
        "date_range": f"{date_min} to {date_max}",
        "n_reps": df["sales_rep"].nunique(),
        "n_cities": total_cities,
        "all_reps_cover_all_cities": all_reps_full_coverage,
        "country_pct": country_pct.to_dict(),
        "top_rep": top_rep,
        "top_rep_sales_per_city": round(top_val),
        "bottom_rep": bottom_rep,
        "bottom_rep_sales_per_city": round(bottom_val),
        "efficiency_gap_pct": round(gap_pct, 1),
        "top_product_class": top_class,
        "top_product_class_pct": float(class_pct.iloc[0]),
        "bottom_product_class": bottom_class,
        "bottom_product_class_pct": float(class_pct.iloc[-1]),
        "leading_team": team_sales.index[0],
        "forecast_rmse_naive": 10_170_583,
        "forecast_rmse_random_forest": 8_466_587,
        "forecast_rmse_improvement_pct": round((1 - 8_466_587 / 10_170_583) * 100, 1),
        "forecast_r2_random_forest": -0.2141,
    }


def build_prompt(facts: dict) -> str:
    facts_json = json.dumps(facts, indent=2)
    return f"""You are a decision analytics consultant writing a 1-page internal \
recommendation memo for a pharma sales leadership team, in the style ZS \
Associates would deliver to a client.

Use ONLY the facts in the JSON block below. Do not invent, estimate, or \
round differently than what is given. Do not add any statistic that is not \
present in this JSON.

FACTS:
{facts_json}

Write the memo with these sections, in this order:
1. **Business Question** — one sentence framing what was investigated (rep/territory effectiveness).
2. **What We Expected vs. What We Found** — state that a territory-coverage-gap hypothesis was tested and disproven (every rep covers all {facts['n_cities']} cities — {facts['all_reps_cover_all_cities']}), and the real finding is a per-rep efficiency gap of {facts['efficiency_gap_pct']}% between {facts['top_rep']} and {facts['bottom_rep']}.
3. **Supporting Evidence** — cite the country concentration split and the product class spread using the exact percentages given.
4. **Forecasting Caveat** — one honest sentence noting the model beat a naive baseline by {facts['forecast_rmse_improvement_pct']}% on RMSE but R2 stayed negative, so it should be read as a directional signal, not a precise forecast.
5. **Recommendation** — reallocate sales-enablement resources toward underperforming reps rather than restructure territories, since coverage is already uniform.

Keep it under 350 words, confident and analytical in tone, no bullet-point \
filler, no hedging phrases like "it seems" or "might suggest" — state findings \
plainly as a consultant would to a client."""


def call_ollama(prompt: str) -> str:
    payload = json.dumps({"model": MODEL, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read())
    return result["response"].strip()


def main():
    df = pd.read_csv(FLAT_CSV)
    facts = compute_facts(df)

    print("Computed facts (grounding the LLM prompt):")
    print(json.dumps(facts, indent=2))

    prompt = build_prompt(facts)
    print(f"\nCalling local LLM ({MODEL} via Ollama)...")
    narrative = call_ollama(prompt)

    header = (
        "# RxIQ — AI-Drafted Recommendation Memo\n\n"
        "*Auto-generated by `scripts/04_ai_insight_narrator.py` using a local "
        f"LLM ({MODEL} via Ollama), grounded in KPIs computed directly from "
        "`rxiq_tableau_flat.csv` with pandas. Review before sending to a "
        "client — this is a first draft, not a final deliverable.*\n\n---\n\n"
    )
    OUT_PATH.write_text(header + narrative + "\n")
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
