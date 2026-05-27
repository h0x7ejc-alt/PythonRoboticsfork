from PathPlanning.TimeBasedPathPlanning.GridWithDynamicObstacles import (
    Grid,
    NodePath,
    ObstacleArrangement,
    Position,
)
from PathPlanning.TimeBasedPathPlanning.BaseClasses import StartAndGoal
from PathPlanning.TimeBasedPathPlanning import PriorityBasedPlanner as m
from PathPlanning.TimeBasedPathPlanning.SafeInterval import SafeIntervalPathPlanner
import numpy as np
import conftest


def test_longest_first_strategy():
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

    planned_start_and_goals, paths = m.PriorityBasedPlanner.plan(grid, start_and_goals, SafeIntervalPathPlanner, False, sort_strategy="longest_first")

    # The first agent planned should have the longest distance
    distances = [sg.distance_start_to_goal() for sg in planned_start_and_goals]
    assert distances == sorted(distances, reverse=True)

    # All paths should start at the specified position and reach the goal
    for i, start_and_goal in enumerate(planned_start_and_goals):
        assert paths[i].path[0].position == start_and_goal.start
        assert paths[i].path[-1].position == start_and_goal.goal

def test_shortest_first_strategy():
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

    planned_start_and_goals, paths = m.PriorityBasedPlanner.plan(grid, start_and_goals, SafeIntervalPathPlanner, False, sort_strategy="shortest_first")

    # The first agent planned should have the shortest distance
    distances = [sg.distance_start_to_goal() for sg in planned_start_and_goals]
    assert distances == sorted(distances, reverse=False)

def test_input_order_strategy():
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

    planned_start_and_goals, paths = m.PriorityBasedPlanner.plan(grid, start_and_goals, SafeIntervalPathPlanner, False, sort_strategy="input_order")

    # The order should be identical to the input
    indices = [sg.index for sg in planned_start_and_goals]
    assert indices == [sg.index for sg in start_and_goals]

def test_failure_return_type():
    from PathPlanning.TimeBasedPathPlanning.BaseClasses import SingleAgentPlanner
    
    class FailingPlanner(SingleAgentPlanner):
        @staticmethod
        def plan(grid, start, goal, verbose=False):
            return None

    grid = Grid(np.array([10, 10]), num_obstacles=0)
    start_and_goals = [StartAndGoal(1, Position(0, 0), Position(9, 9))]
    
    planned_start_and_goals, paths = m.PriorityBasedPlanner.plan(grid, start_and_goals, FailingPlanner, False)
    
    assert isinstance(planned_start_and_goals, list)
    assert isinstance(paths, list)
    assert len(planned_start_and_goals) == 0
    assert len(paths) == 0

if __name__ == "__main__":
    conftest.run_this_test(__file__)
