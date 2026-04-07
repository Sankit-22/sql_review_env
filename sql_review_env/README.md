---
title: SQL Review Environment
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
tags:
  - openenv
---

# SQL Review Environment

A real-world OpenEnv environment where an AI agent must review and fix broken SQL queries. Tasks range from simple syntax errors to complex security vulnerabilities and logic bugs.

This environment is useful for training and evaluating AI agents on real data engineering tasks that developers face daily.

## Environment Description

SQL query review and debugging is a task that every data engineer and backend developer performs regularly. Broken queries, missing clauses, and SQL injection vulnerabilities are common real-world problems. This environment simulates exactly that — the agent receives a broken SQL query and must fix it correctly.

## API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/reset` | POST | Reset environment for a given task |
| `/step` | POST | Submit a SQL fix and get scored |
| `/state` | GET | Get current episode state |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive Swagger UI |

### Request Format

**POST /reset**
```json
{"task_id": "easy_001"}
```

**POST /step**
```json
{"action": {"sql": "SELECT * FROM users WHERE age > 18"}}
```

## Action Space

**SqlReviewAction**

| Field | Type | Description |
| --- | --- | --- |
| `sql` | string | The fixed SQL query submitted by the agent |

## Observation Space

**SqlReviewObservation**

| Field | Type | Description |
| --- | --- | --- |
| `task_id` | string | Current task identifier |
| `task_description` | string | What the agent needs to fix |
| `broken_sql` | string | The broken SQL query to fix |
| `feedback` | string | Detailed feedback on the submission |
| `score` | float | Score between 0.0 and 1.0 |
| `done` | boolean | Whether all tasks are complete |
| `expected_output` | string | Hint about what correct output looks like |

## Tasks

### Task 1 — Easy: Syntax Fix

* **ID:** `easy_001`
* **Description:** Fix syntax errors in a broken SELECT query (typos in keywords)
* **Broken SQL:** `SELEC * FORM users WHEREE age > 18`
* **Expected:** Return all users older than 18
* **Difficulty:** Easy — tests basic SQL keyword knowledge

### Task 2 — Medium: Missing GROUP BY

* **ID:** `medium_001`
* **Description:** Fix a query missing a GROUP BY clause in an aggregation
* **Broken SQL:** `SELECT customer_id, SUM(amount) as total FROM orders`
* **Expected:** Return total order amount per customer
* **Difficulty:** Medium — tests understanding of SQL aggregation

### Task 3 — Hard: Security + Logic Bug

* **ID:** `hard_001`
* **Description:** Fix a SQL injection vulnerability AND a logic error (OR → AND)
* **Broken SQL:** `SELECT * FROM admins WHERE role = 'admin' OR is_active = 1`
* **Expected:** Return only users who are BOTH admins AND active
* **Difficulty:** Hard — tests security awareness and logic correctness

## Reward Function

Rewards provide partial progress signals across the full trajectory:

| Condition | Reward |
| --- | --- |
| SELECT keyword present | +0.2 |
| FROM keyword present | +0.2 |
| Query executes without error | +0.2 |
| Correct rows returned | +0.3 |
| GROUP BY present (medium task) | +0.3 |
| AND logic fix correct (hard task) | +0.3 |
| Injection fixed (hard task) | +0.3 |

Total score range: **0.0 to 1.0** per task.

## Baseline Scores

Verified by live testing against the deployed HF Space using `gpt-4o-mini`:

| Task | Difficulty | Model | Score |
| --- | --- | --- | --- |
| `easy_001` | Easy | gpt-4o-mini | 1.00 |
| `medium_001` | Medium | gpt-4o-mini | 1.00 |
| `hard_001` | Hard | gpt-4o-mini | 0.60 |
| **Average** | | | **0.87** |

## Setup & Usage

### Prerequisites

* Python 3.10+
* Docker Desktop
* OpenAI API key (for inference script)

### Environment Variables

| Variable | Description |
| --- | --- |
| `API_BASE_URL` | LLM API endpoint (e.g. `https://api.openai.com/v1`) |
| `MODEL_NAME` | Model identifier (e.g. `gpt-4o-mini`) |
| `HF_TOKEN` | Your OpenAI / HuggingFace API key |

### Run inference script

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_key_here
python inference.py
```

### Run locally with Docker

```bash
docker build -t sql_review_env:latest .
docker run -p 8000:8000 sql_review_env:latest
```

### Quick API test

```bash
# Reset
curl -X POST https://sanket-bharga22va-sql-review-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_001"}'

# Step
curl -X POST https://sanket-bharga22va-sql-review-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"sql": "SELECT * FROM users WHERE age > 18"}}'

# State
curl https://sanket-bharga22va-sql-review-env.hf.space/state
```

## Project Structure

```
sql_review_env/
├── inference.py          ← mandatory evaluation script
├── baseline.py           ← local dev script
├── README.md
├── openenv.yaml
├── pyproject.toml
├── models.py
├── client.py
├── Dockerfile
└── server/
    ├── app.py
    ├── sql_review_env_environment.py
    └── requirements.txt
```
