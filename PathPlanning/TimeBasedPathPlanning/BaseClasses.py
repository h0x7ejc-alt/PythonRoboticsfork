from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, TypeAlias
from PathPlanning.TimeBasedPathPlanning.GridWithDynamicObstacles import (
    Grid,
    Position,
)
from PathPlanning.TimeBasedPathPlanning.Node import NodePath
import random
import numpy.random as numpy_random

PriorityBasedPlanningStrategy: TypeAlias = Literal[
    "longest_first", "shortest_first", "input_order"
]

# Seed randomness for reproducibility
RANDOM_SEED = 50
random.seed(RANDOM_SEED)
numpy_random.seed(RANDOM_SEED)

class SingleAgentPlanner(ABC):
    """
    Base class for single agent planners
    """

    @staticmethod
    @abstractmethod
    def plan(grid: Grid, start: Position, goal: Position, verbose: bool = False) -> NodePath:
        pass

@dataclass
class StartAndGoal:
    index: int
    start: Position
    goal: Position

    def distance_start_to_goal(self) -> float:
        return pow(self.goal.x - self.start.x, 2) + pow(self.goal.y - self.start.y, 2)

class MultiAgentPlanner(ABC):
    """
    Base class for multi-agent planners
    """

    @staticmethod
    @abstractmethod
    def plan(
        grid: Grid,
        start_and_goal_positions: list[StartAndGoal],
        single_agent_planner_class: SingleAgentPlanner,
        verbose: bool = False,
        priority_order_strategy: PriorityBasedPlanningStrategy = "longest_first",
    ) -> tuple[list[StartAndGoal], list[NodePath]]:
        """
        Plan for all agents. Returned paths are in order corresponding to the returned list of `StartAndGoal` objects
        """
        pass
