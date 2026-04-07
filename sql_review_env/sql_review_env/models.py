# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the SQL Review Environment.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from typing import Optional


class SqlReviewAction(Action):
    """Action for the SQL Review environment - submit a SQL query."""

    sql: str = Field(..., description="The SQL query submitted by the agent")


class SqlReviewObservation(Observation):
    """Observation returned after each step."""

    task_id: str = Field(default="", description="Current task identifier")
    task_description: str = Field(default="", description="Description of the task to solve")
    broken_sql: str = Field(default="", description="The SQL query that needs to be fixed")
    feedback: str = Field(default="", description="Feedback on the submitted SQL")
    score: float = Field(default=0.0, description="Current score between 0.0 and 1.0")
    done: bool = Field(default=False, description="Whether the task is completed")
    expected_output: Optional[str] = Field(default=None, description="Expected query result hint")