# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
SQL Review Environment Implementation.

A real-world environment where an AI agent must review and fix SQL queries.
Tasks range from simple syntax fixes to complex security vulnerability detection.
"""

import sqlite3
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import SqlReviewAction, SqlReviewObservation
except ImportError:
    from models import SqlReviewAction, SqlReviewObservation


TASKS = [
    {
        "task_id": "easy_001",
        "description": (
            "Fix the syntax error in this SQL query. "
            "The query should select all users who are older than 18."
        ),
        "broken_sql": "SELEC * FORM users WHEREE age > 18",
        "expected_output": "Should return all rows from users table where age > 18",
        "difficulty": "easy",
        "setup_sql": [
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)",
            "INSERT OR IGNORE INTO users VALUES (1, 'Alice', 25)",
            "INSERT OR IGNORE INTO users VALUES (2, 'Bob', 17)",
            "INSERT OR IGNORE INTO users VALUES (3, 'Charlie', 30)",
        ],
        "expected_rows": 2,
    },
    {
        "task_id": "medium_001",
        "description": (
            "This query is supposed to get the total order amount per customer, "
            "but it is missing a GROUP BY clause. Fix it."
        ),
        "broken_sql": "SELECT customer_id, SUM(amount) as total FROM orders",
        "expected_output": "Should return customer_id and total amount grouped per customer",
        "difficulty": "medium",
        "setup_sql": [
            "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL)",
            "INSERT OR IGNORE INTO orders VALUES (1, 1, 100.0)",
            "INSERT OR IGNORE INTO orders VALUES (2, 1, 200.0)",
            "INSERT OR IGNORE INTO orders VALUES (3, 2, 150.0)",
        ],
        "expected_rows": 2,
    },
    {
        "task_id": "hard_001",
        "description": (
            "This query has a logic error. "
            "Fix it so only active admins are returned. "
            "The WHERE clause uses OR instead of AND — fix it."
        ),
        "broken_sql": "SELECT * FROM admins WHERE role = 'admin' OR is_active = 1",
        "expected_output": "Should return only users who are BOTH admins AND active",
        "difficulty": "hard",
        "setup_sql": [
            "CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, name TEXT, role TEXT, is_active INTEGER)",
            "INSERT OR IGNORE INTO admins VALUES (1, 'Alice', 'admin', 1)",
            "INSERT OR IGNORE INTO admins VALUES (2, 'Bob', 'user', 1)",
            "INSERT OR IGNORE INTO admins VALUES (3, 'Charlie', 'admin', 0)",
        ],
        "expected_rows": 1,
    },
]


def setup_db(conn, setup_sql_list):
    cursor = conn.cursor()
    for sql in setup_sql_list:
        cursor.execute(sql)
    conn.commit()


def run_query(conn, sql):
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall(), None
    except Exception as e:
        return None, str(e)


def grade_easy(sql, conn):
    reward = 0.0
    feedback = []

    sql_upper = sql.upper().strip()
    if "SELECT" in sql_upper:
        reward += 0.2
        feedback.append("✓ SELECT keyword present")
    if "FROM" in sql_upper:
        reward += 0.2
        feedback.append("✓ FROM keyword present")
    if "WHERE" in sql_upper:
        reward += 0.1
        feedback.append("✓ WHERE clause present")

    rows, error = run_query(conn, sql)
    if error:
        feedback.append(f"✗ Query error: {error}")
    else:
        reward += 0.2
        feedback.append("✓ Query executes without error")
        if len(rows) == 2:
            reward += 0.3
            feedback.append("✓ Correct number of rows returned!")
        else:
            feedback.append(f"✗ Expected 2 rows, got {len(rows)}")

    return round(min(reward, 1.0), 2), " | ".join(feedback)


def grade_medium(sql, conn):
    reward = 0.0
    feedback = []

    sql_upper = sql.upper().strip()
    if "GROUP BY" in sql_upper:
        reward += 0.3
        feedback.append("✓ GROUP BY present")
    else:
        feedback.append("✗ Missing GROUP BY clause")

    if "SUM" in sql_upper:
        reward += 0.1
        feedback.append("✓ SUM aggregation present")

    rows, error = run_query(conn, sql)
    if error:
        feedback.append(f"✗ Query error: {error}")
    else:
        reward += 0.3
        feedback.append("✓ Query executes without error")
        if len(rows) == 2:
            reward += 0.3
            feedback.append("✓ Correct number of groups returned!")
        else:
            feedback.append(f"✗ Expected 2 groups, got {len(rows)}")

    return round(min(reward, 1.0), 2), " | ".join(feedback)


def grade_hard(sql, conn):
    reward = 0.0
    feedback = []

    sql_upper = sql.upper().strip()

    if " AND " in sql_upper and " OR " not in sql_upper:
        reward += 0.4
        feedback.append("✓ Logic fix correct: AND used instead of OR")
    else:
        feedback.append("✗ Logic error: should use AND not OR")

    rows, error = run_query(conn, sql)
    if error:
        feedback.append(f"✗ Query error: {error}")
    else:
        reward += 0.2
        feedback.append("✓ Query executes without error")
        if len(rows) == 1:
            reward += 0.4
            feedback.append("✓ Correct result: only 1 active admin returned!")
        else:
            feedback.append(f"✗ Expected 1 row, got {len(rows)}")

    return round(min(reward, 1.0), 2), " | ".join(feedback)


GRADERS = {
    "easy_001": grade_easy,
    "medium_001": grade_medium,
    "hard_001": grade_hard,
}


class SqlReviewEnvironment(Environment):
    """
    SQL Review Environment.

    An agent must fix broken SQL queries across 3 difficulty levels.
    Rewards are given for partial progress — syntax, execution, and correctness.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_task_index = 0
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._load_task(self._current_task_index)

    def _load_task(self, index):
        task = TASKS[index]
        setup_db(self._conn, task["setup_sql"])
        self._current_task = task

    def reset(self) -> SqlReviewObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_task_index = 0
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._load_task(0)
        task = self._current_task
        return SqlReviewObservation(
            task_id=task["task_id"],
            task_description=task["description"],
            broken_sql=task["broken_sql"],
            feedback="Environment reset. Fix the SQL query above.",
            score=0.0,
            done=False,
            expected_output=task["expected_output"],
            reward=0.0,
        )

    def step(self, action: SqlReviewAction) -> SqlReviewObservation:
        self._state.step_count += 1
        task = self._current_task
        grader = GRADERS[task["task_id"]]
        score, feedback = grader(action.sql, self._conn)

        done = False
        if score >= 0.9:
            self._current_task_index += 1
            if self._current_task_index >= len(TASKS):
                done = True
                feedback += " | 🎉 All tasks complete!"
            else:
                self._conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._load_task(self._current_task_index)
                task = self._current_task
                feedback += f" | ✓ Moving to next task: {task['task_id']}"

        return SqlReviewObservation(
            task_id=self._current_task["task_id"],
            task_description=self._current_task["description"],
            broken_sql=self._current_task["broken_sql"],
            feedback=feedback,
            score=score,
            done=done,
            expected_output=self._current_task["expected_output"],
            reward=score,
        )

    @property
    def state(self) -> State:
        return self._state