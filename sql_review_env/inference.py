"""
inference.py — OpenEnv SQL Review Environment
Mandatory inference script for evaluation.

Reads credentials from environment variables:
  API_BASE_URL  : LLM API endpoint (e.g. https://api.openai.com/v1)
  MODEL_NAME    : Model identifier  (e.g. gpt-4o-mini)
  HF_TOKEN      : HuggingFace / API key used as the bearer token

Emits structured stdout logs in [START] / [STEP] / [END] format.
Calls the live HF Space REST API — does NOT import env code directly.
"""

import os
import json
import requests
from openai import OpenAI

# ── Credentials & config ─────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN",     os.environ.get("OPENAI_API_KEY", ""))

ENV_BASE_URL = "https://sanket-bharga22va-sql-review-env.hf.space"

# Task IDs in order (easy → medium → hard)
TASK_IDS = ["easy_001", "medium_001", "hard_001"]

# ── OpenAI client ────────────────────────────────────────────────────────────
client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

SYSTEM_PROMPT = (
    "You are an expert SQL developer. "
    "You will be given a broken SQL query and a task description. "
    "Your job is to fix the SQL query. "
    "Reply with ONLY the fixed SQL query — no explanations, no markdown, just raw SQL."
)

# ── Helper: unwrap nested API response ───────────────────────────────────────

def unwrap(response: dict) -> dict:
    """
    The API returns:
      { "observation": { "task_id": ..., "broken_sql": ..., ... }, "reward": 0, "done": false }
    This unwraps it into a flat dict, merging top-level fields in.
    """
    obs = response.get("observation", response)  # fallback to flat if no nesting
    obs["reward"] = response.get("reward", obs.get("reward", 0.0))
    obs["done"]   = response.get("done",   obs.get("done", False))
    obs["score"]  = obs.get("score", response.get("reward", 0.0))
    return obs


# ── Env API calls ─────────────────────────────────────────────────────────────

def env_reset(task_id: str) -> dict:
    """Call POST /reset on the live environment."""
    resp = requests.post(
        f"{ENV_BASE_URL}/reset",
        json={"task_id": task_id},
        timeout=30,
    )
    resp.raise_for_status()
    return unwrap(resp.json())


def env_step(sql: str) -> dict:
    """Call POST /step on the live environment.
    API requires action wrapped: {"action": {"sql": "..."}}
    """
    resp = requests.post(
        f"{ENV_BASE_URL}/step",
        json={"action": {"sql": sql}},  # ← correct wrapper
        timeout=30,
    )
    resp.raise_for_status()
    return unwrap(resp.json())


def env_state() -> dict:
    """Call GET /state on the live environment."""
    resp = requests.get(f"{ENV_BASE_URL}/state", timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── LLM call ──────────────────────────────────────────────────────────────────

def get_fixed_sql(task_description: str, broken_sql: str) -> str:
    """Ask the LLM to fix the broken SQL query."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Task: {task_description}\n\n"
                    f"Broken SQL:\n{broken_sql}\n\n"
                    "Fixed SQL:"
                ),
            },
        ],
        temperature=0,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


# ── Main loop ─────────────────────────────────────────────────────────────────

def run():
    all_scores = []

    for task_id in TASK_IDS:

        # ── RESET ─────────────────────────────────────────────────────────────
        obs = env_reset(task_id)

        # Emit [START] log
        start_log = {
            "task_id":          obs.get("task_id", task_id),
            "task_description": obs.get("task_description", ""),
            "broken_sql":       obs.get("broken_sql", ""),
        }
        print(f"[START] {json.dumps(start_log)}", flush=True)

        step_num   = 0
        done       = obs.get("done", False)
        last_score = 0.0

        # ── STEP LOOP ─────────────────────────────────────────────────────────
        while not done:
            step_num += 1

            # Agent decides action
            fixed_sql = get_fixed_sql(
                obs.get("task_description", ""),
                obs.get("broken_sql", ""),
            )

            # Submit action to env
            obs = env_step(fixed_sql)

            last_score = obs.get("score", 0.0)
            done       = obs.get("done", False)

            # Emit [STEP] log
            step_log = {
                "step":     step_num,
                "task_id":  obs.get("task_id", task_id),
                "action":   fixed_sql,
                "score":    last_score,
                "done":     done,
                "feedback": obs.get("feedback", ""),
            }
            print(f"[STEP] {json.dumps(step_log)}", flush=True)

            # Single-step tasks finish after one action
            if done or step_num >= 1:
                break

        all_scores.append(last_score)

        # Emit [END] log per task
        end_log = {
            "task_id": task_id,
            "score":   last_score,
            "steps":   step_num,
        }
        print(f"[END] {json.dumps(end_log)}", flush=True)

    # ── Final summary ─────────────────────────────────────────────────────────
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    summary = {
        "total_tasks":   len(TASK_IDS),
        "scores":        dict(zip(TASK_IDS, all_scores)),
        "average_score": round(avg_score, 4),
    }
    print(f"[END] {json.dumps(summary)}", flush=True)


if __name__ == "__main__":
    run()
