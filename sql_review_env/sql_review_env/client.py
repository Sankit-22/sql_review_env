# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""SQL Review Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import SqlReviewAction, SqlReviewObservation


class SqlReviewEnv(
    EnvClient[SqlReviewAction, SqlReviewObservation, State]
):
    """
    Client for the SQL Review Environment.

    The agent must fix broken SQL queries across 3 difficulty levels:
    easy (syntax fix), medium (missing GROUP BY), hard (injection + logic bug).

    Example:
        >>> with SqlReviewEnv(base_url="http://localhost:8000").sync() as client:
        ...     result = client.reset()
        ...     print(result.observation.task_description)
        ...     result = client.step(SqlReviewAction(sql="SELECT * FROM users WHERE age > 18"))
        ...     print(result.observation.feedback)
    """

    def _step_payload(self, action: SqlReviewAction) -> Dict:
        return {
            "sql": action.sql,
        }

    def _parse_result(self, payload: Dict) -> StepResult[SqlReviewObservation]:
        obs_data = payload.get("observation", {})
        observation = SqlReviewObservation(
            task_id=obs_data.get("task_id", ""),
            task_description=obs_data.get("task_description", ""),
            broken_sql=obs_data.get("broken_sql", ""),
            feedback=obs_data.get("feedback", ""),
            score=obs_data.get("score", 0.0),
            done=payload.get("done", False),
            expected_output=obs_data.get("expected_output", ""),
            reward=payload.get("reward", 0.0),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )