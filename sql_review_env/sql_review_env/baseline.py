# Baseline inference script for SQL Review Environment
# Reads OPENAI_API_KEY from environment variables
# Runs a model against all 3 tasks and produces reproducible scores

import os
import sqlite3
from openai import OpenAI

from models import SqlReviewAction, SqlReviewObservation
from server.sql_review_env_environment import SqlReviewEnvironment

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an expert SQL developer. You will be given a broken SQL query and a task description.
Your job is to fix the SQL query. Reply with ONLY the fixed SQL query, nothing else. No explanations, no markdown, just the raw SQL."""

def get_fixed_sql(task_description: str, broken_sql: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Task: {task_description}\n\nBroken SQL: {broken_sql}\n\nFixed SQL:"}
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def run_baseline():
    print("=" * 60)
    print("SQL Review Environment - Baseline Inference Script")
    print("=" * 60)

    env = SqlReviewEnvironment()
    obs = env.reset()

    results = []
    task_num = 1

    while True:
        print(f"\n📋 Task {task_num}: {obs.task_id}")
        print(f"   Description: {obs.task_description}")
        print(f"   Broken SQL:  {obs.broken_sql}")

        fixed_sql = get_fixed_sql(obs.task_description, obs.broken_sql)
        print(f"   Agent SQL:   {fixed_sql}")

        action = SqlReviewAction(sql=fixed_sql)
        step_result = env.step(action)
        obs = step_result

        print(f"   Score:       {obs.score}")
        print(f"   Feedback:    {obs.feedback}")

        results.append({
            "task_id": obs.task_id,
            "score": obs.score,
        })

        if obs.done or task_num >= 3:
            break

        task_num += 1

    print("\n" + "=" * 60)
    print("BASELINE RESULTS")
    print("=" * 60)
    total = 0.0
    for r in results:
        print(f"  {r['task_id']}: {r['score']:.2f}")
        total += r['score']
    avg = total / len(results) if results else 0.0
    print(f"\n  Average Score: {avg:.2f}")
    print("=" * 60)


if __name__ == "__main__":
    run_baseline()