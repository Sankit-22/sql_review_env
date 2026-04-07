---
title: SQL Review Environment
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# SQL Review Environment

A real-world OpenEnv environment where an AI agent must review and fix broken SQL queries. Tasks range from simple syntax errors to complex security vulnerabilities and logic bugs.

This environment is useful for training and evaluating AI agents on real data engineering tasks that developers face daily.

## Environment Description

SQL query review and debugging is a task that every data engineer and backend developer performs regularly. Broken queries, missing clauses, and SQL injection vulnerabilities are common real-world problems. This environment simulates exactly that — the agent receives a broken SQL query and must fix it correctly.

## Action Space

**SqlReviewAction**
| Field | Type | Description |
|-------|------|-------------|
| `sql` | string | The fixed SQL query submitted by the agent |

## Observation Space

**SqlReviewObservation**
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Current task identifier |
| `task_description` | string | What the agent needs to fix |
| `broken_sql` | string | The broken SQL query to fix |
| `feedback` | string | Detailed feedback on the submission |
| `score` | float | Score between 0.0 and 1.0 |
| `done` | boolean | Whether all tasks are complete |
| `expected_output` | string | Hint about what correct output looks like |

## Tasks

### Task 1 — Easy: Syntax Fix
- **ID:** `easy_001`
- **Description:** Fix syntax errors in a broken SELECT query (typos in keywords)
- **Broken SQL:** `SELEC * FORM users WHEREE age > 18`
- **Expected:** Return all users older than 18
- **Difficulty:** Easy — tests basic SQL keyword knowledge

### Task 2 — Medium: Missing GROUP BY
- **ID:** `medium_001`
- **Description:** Fix a query missing a GROUP BY clause in an aggregation
- **Broken SQL:** `SELECT customer_id, SUM(amount) as total FROM orders`
- **Expected:** Return total order amount per customer
- **Difficulty:** Medium — tests understanding of SQL aggregation

### Task 3 — Hard: Security + Logic Bug
- **ID:** `hard_001`
- **Description:** Fix a SQL injection vulnerability AND a logic error (OR → AND)
- **Broken SQL:** `SELECT * FROM admins WHERE role = 'admin' OR is_active = 1`
- **Expected:** Return only users who are BOTH admins AND active
- **Difficulty:** Hard — tests security awareness and logic correctness

## Reward Function

Rewards provide partial progress signals across the full trajectory:

| Condition | Reward |
|-----------|--------|
| SELECT keyword present | +0.2 |
| FROM keyword present | +0.2 |
| Query executes without error | +0.2 |
| Correct rows returned | +0.3 |
| GROUP BY present (medium) | +0.3 |
| Logic fix correct (hard) | +0.3 |
| Injection fixed (hard) | +0.3 |

Total score range: **0.0 to 1.0** per task.

## Baseline Scores

| Task | Model | Score |
|------|-------|-------|
| easy_001 | gpt-4o-mini | 1.00 |
| medium_001 | gpt-4o-mini | 0.90 |
| hard_001 | gpt-4o-mini | 0.60 |
| **Average** | | **0.83** |

## Setup & Usage

### Prerequisites
- Python 3.10+
- Docker Desktop
- OpenAI API key (for baseline script)

### Install dependencies
```bash
pip install openenv-core
```

### Run locally with Docker
```bash
docker build -t sql_review_env:latest -f server/Dockerfile .
docker run -p 8000:8000 sql_review_env:latest
```

### Run baseline script
```bash
export OPENAI_API_KEY=your_key_here
python baseline.py
```

### Use the client
```python
from sql_review_env import SqlReviewAction, SqlReviewEnv

with SqlReviewEnv(base_url="http://localhost:8000").sync() as env:
    result = env.reset()
    print(result.observation.task_description)

    result = env.step(SqlReviewAction(sql="SELECT * FROM users WHERE age > 18"))
    print(result.observation.feedback)
    print(result.observation.score)
```

## Project Structure
```
sql_review_env/
├── __init__.py
├── README.md
├── openenv.yaml
├── pyproject.toml
├── models.py
├── client.py
├── baseline.py
└── server/
    ├── app.py
    ├── sql_review_env_environment.py
    ├── requirements.txt
    └── Dockerfile
```