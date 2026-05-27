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


def create_test_grid_and_agents(grid_side_length=21, num_agents=15):
    start_and_goals = [StartAndGoal(i, Position(1, i), Position(19, 19-i)) for i in range(1, num_agents+1)]
    obstacle_avoid_points = [pos for item in start_and_goals for pos in (item.start, item.goal)]
    
    grid = Grid(
        np.array([grid_side_length, grid_side_length]),
        num_obstacles=250,
        obstacle_avoid_points=obstacle_avoid_points,
        obstacle_arrangement=ObstacleArrangement.ARRANGEMENT1,
    )
    
    return grid, start_and_goals


def verify_paths(start_and_goals, paths):
    # All paths should start at the specified position and reach the goal
    for i, start_and_goal in enumerate(start_and_goals):
        assert paths[i].path[0].position == start_and_goal.start
        assert paths[i].path[-1].position == start_and_goal.goal


def test_default_strategy_longest_first():
    """Test the default strategy (longest_first)"""
    m.show_animation = False
    grid, start_and_goals = create_test_grid_and_agents()
    
    # Test with default strategy
    ordered_agents, paths = m.PriorityBasedPlanner.plan(grid, start_and_goals, SafeIntervalPathPlanner, False)
    verify_paths(ordered_agents, paths)


def test_strategy_shortest_first():
    """Test shortest_first strategy"""
    m.show_animation = False
    grid, start_and_goals = create_test_grid_and_agents()
    
    ordered_agents, paths = m.PriorityBasedPlanner.plan(grid, start_and_goals, SafeIntervalPathPlanner, False, order_strategy="shortest_first")
    verify_paths(ordered_agents, paths)


def test_strategy_input_order():
    """Test input_order strategy"""
    m.show_animation = False
    grid, start_and_goals = create_test_grid_and_agents()
    
    ordered_agents, paths = m.PriorityBasedPlanner.plan(grid, start_and_goals, SafeIntervalPathPlanner, False, order_strategy="input_order")
    verify_paths(ordered_agents, paths)
    
    # Verify the order remains the same as input
    for i in range(len(start_and_goals)):
        assert ordered_agents[i].index == start_and_goals[i].index


def test_invalid_strategy():
    """Test invalid strategy raises ValueError"""
    m.show_animation = False
    grid, start_and_goals = create_test_grid_and_agents(num_agents=2)
    
    try:
        m.PriorityBasedPlanner.plan(grid, start_and_goals, SafeIntervalPathPlanner, False, order_strategy="invalid_strategy")
        assert False, "Expected ValueError was not raised"
    except ValueError as e:
        assert "Unknown order strategy" in str(e)


if __name__ == "__main__":
    conftest.run_this_test(__file__)
