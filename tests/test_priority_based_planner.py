from PathPlanning.TimeBasedPathPlanning.GridWithDynamicObstacles import (
    Grid,
    NodePath,
    ObstacleArrangement,
    Position,
)
from PathPlanning.TimeBasedPathPlanning.BaseClasses import StartAndGoal
from PathPlanning.TimeBasedPathPlanning import PriorityBasedPlanner as m
from PathPlanning.TimeBasedPathPlanning.Node import Node
from PathPlanning.TimeBasedPathPlanning.SafeInterval import SafeIntervalPathPlanner
import numpy as np
import conftest


def build_grid(grid_side_length: int = 21) -> Grid:
    return Grid(
        np.array([grid_side_length, grid_side_length]),
        num_obstacles=0,
        obstacle_arrangement=ObstacleArrangement.RANDOM,
        time_limit=20,
    )


def build_start_and_goals() -> list[StartAndGoal]:
    return [
        StartAndGoal(7, Position(0, 0), Position(0, 4)),
        StartAndGoal(3, Position(1, 0), Position(1, 1)),
        StartAndGoal(11, Position(2, 0), Position(2, 2)),
    ]


class RecordingPlanner:
    call_order: list[int] = []

    @staticmethod
    def plan(grid: Grid, start: Position, goal: Position, verbose: bool = False) -> NodePath:
        RecordingPlanner.call_order.append(start.x)
        return NodePath([
            Node(start, 0, 0, -1),
            Node(goal, 1, 0, 0),
        ], 0)


class FailingPlanner:
    @staticmethod
    def plan(grid: Grid, start: Position, goal: Position, verbose: bool = False) -> NodePath:
        if goal == Position(2, 2):
            raise Exception("No path found")

        return NodePath([
            Node(start, 0, 0, -1),
            Node(goal, 1, 0, 0),
        ], 0)


def test_plan_default_strategy_matches_longest_first_order():
    grid = build_grid()
    start_and_goals = build_start_and_goals()

    RecordingPlanner.call_order = []
    ordered_start_and_goals, paths = m.PriorityBasedPlanner.plan(
        grid,
        start_and_goals,
        RecordingPlanner,
    )

    assert [item.index for item in ordered_start_and_goals] == [7, 11, 3]
    assert RecordingPlanner.call_order == [0, 2, 1]
    assert [path.path[0].position for path in paths] == [item.start for item in ordered_start_and_goals]


def test_plan_supports_shortest_first_order():
    grid = build_grid()
    start_and_goals = build_start_and_goals()

    RecordingPlanner.call_order = []
    ordered_start_and_goals, _ = m.PriorityBasedPlanner.plan(
        grid,
        start_and_goals,
        RecordingPlanner,
        priority_order_strategy="shortest_first",
    )

    assert [item.index for item in ordered_start_and_goals] == [3, 11, 7]
    assert RecordingPlanner.call_order == [1, 2, 0]


def test_plan_supports_input_order():
    grid = build_grid()
    start_and_goals = build_start_and_goals()

    RecordingPlanner.call_order = []
    ordered_start_and_goals, _ = m.PriorityBasedPlanner.plan(
        grid,
        start_and_goals,
        RecordingPlanner,
        priority_order_strategy="input_order",
    )

    assert [item.index for item in ordered_start_and_goals] == [7, 3, 11]
    assert RecordingPlanner.call_order == [0, 1, 2]


def test_plan_returns_stable_tuple_when_agent_planning_fails():
    grid = build_grid()
    start_and_goals = build_start_and_goals()

    result = m.PriorityBasedPlanner.plan(
        grid,
        start_and_goals,
        FailingPlanner,
    )

    assert isinstance(result, tuple)

    planned_start_and_goals, paths = result
    assert [item.index for item in planned_start_and_goals] == [7]
    assert len(paths) == 1
    assert paths[0].path[-1].position == planned_start_and_goals[0].goal


def test_plan_with_safe_interval_planner_reaches_each_goal():
    grid_side_length = 21

    start_and_goals = [StartAndGoal(i, Position(1, i), Position(19, 19-i)) for i in range(1, 16)]
    obstacle_avoid_points = [pos for item in start_and_goals for pos in (item.start, item.goal)]

    grid = Grid(
        np.array([grid_side_length, grid_side_length]),
        num_obstacles=250,
        obstacle_avoid_points=obstacle_avoid_points,
        obstacle_arrangement=ObstacleArrangement.ARRANGEMENT1,
    )

    m.show_animation = False

    ordered_start_and_goals, paths = m.PriorityBasedPlanner.plan(
        grid,
        start_and_goals,
        SafeIntervalPathPlanner,
        False,
    )

    assert len(ordered_start_and_goals) == len(paths)
    assert [item.distance_start_to_goal() for item in ordered_start_and_goals] == sorted(
        [item.distance_start_to_goal() for item in ordered_start_and_goals],
        reverse=True,
    )

    for i, start_and_goal in enumerate(ordered_start_and_goals):
        assert paths[i].path[0].position == start_and_goal.start
        assert paths[i].path[-1].position == start_and_goal.goal


if __name__ == "__main__":
    conftest.run_this_test(__file__)
