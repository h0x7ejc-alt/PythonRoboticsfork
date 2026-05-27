#!/usr/bin/env python3
"""Test script for RetryUntilSuccessful node."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from MissionPlanning.BehaviorTree.behavior_tree import (
    BehaviorTreeFactory,
    Status,
    ActionNode,
)


def test_retry():
    print("Testing RetryUntilSuccessful node...")

    class SuccessAfterNNode(ActionNode):
        def __init__(self, name, n):
            super().__init__(name)
            self.count = 0
            self.n = n

        def tick(self):
            self.count += 1
            print(f"  SuccessAfterN tick: {self.count}/{self.n}")
            if self.count >= self.n:
                return Status.SUCCESS
            else:
                return Status.FAILURE

    xml_string = """
        <RetryUntilSuccessful num_attempts="5">
            <SuccessAfterN name="Test" n="3" />
        </RetryUntilSuccessful>
    """

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "SuccessAfterN",
        lambda node: SuccessAfterNNode(
            node.attrib.get("name", SuccessAfterNNode.__name__),
            int(node.attrib["n"]),
        ),
    )
    bt = bt_factory.build_tree(xml_string)

    print("\nTest 1: Child eventually succeeds:")
    bt.tick()
    print(f"  Status: {bt.root.status}")
    assert bt.root.status == Status.RUNNING

    bt.tick()
    print(f"  Status: {bt.root.status}")
    assert bt.root.status == Status.RUNNING

    bt.tick()
    print(f"  Status: {bt.root.status}")
    assert bt.root.status == Status.SUCCESS

    print("\n✓ Test 1 passed!")

    print("\nTest 2: Child always fails:")

    class AlwaysFailNode(ActionNode):
        def __init__(self, name):
            super().__init__(name)
            self.tick_count = 0

        def tick(self):
            self.tick_count += 1
            print(f"  AlwaysFail tick: {self.tick_count}")
            return Status.FAILURE

    xml_string2 = """
        <RetryUntilSuccessful num_attempts="3">
            <AlwaysFail name="Test" />
        </RetryUntilSuccessful>
    """

    bt_factory2 = BehaviorTreeFactory()
    bt_factory2.register_node_builder(
        "AlwaysFail",
        lambda node: AlwaysFailNode(
            node.attrib.get("name", AlwaysFailNode.__name__),
        ),
    )
    bt2 = bt_factory2.build_tree(xml_string2)

    bt2.tick()
    print(f"  Status: {bt2.root.status}")
    assert bt2.root.status == Status.RUNNING

    bt2.tick()
    print(f"  Status: {bt2.root.status}")
    assert bt2.root.status == Status.RUNNING

    bt2.tick()
    print(f"  Status: {bt2.root.status}")
    assert bt2.root.status == Status.FAILURE

    print("\n✓ Test 2 passed!")

    print("\nAll tests passed! ✓")


if __name__ == "__main__":
    test_retry()
