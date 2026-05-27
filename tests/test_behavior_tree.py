import pytest
import conftest

from MissionPlanning.BehaviorTree.behavior_tree import (
    BehaviorTreeFactory,
    Status,
    ActionNode,
)


def test_sequence_node1():
    xml_string = """
        <Sequence>
            <Echo name="Echo 1" message="Hello, World1!" />
            <Echo name="Echo 2" message="Hello, World2!" />
            <ForceFailure name="Force Failure">
                <Echo name="Echo 3" message="Hello, World3!" />
            </ForceFailure>
        </Sequence>
    """
    bt_factory = BehaviorTreeFactory()
    bt = bt_factory.build_tree(xml_string)
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status == Status.SUCCESS
    assert bt.root.children[1].status is None
    assert bt.root.children[2].status is None
    bt.tick()
    bt.tick()
    assert bt.root.status == Status.FAILURE
    assert bt.root.children[0].status is None
    assert bt.root.children[1].status is None
    assert bt.root.children[2].status is None


def test_sequence_node2():
    xml_string = """
        <Sequence>
            <Echo name="Echo 1" message="Hello, World1!" />
            <Echo name="Echo 2" message="Hello, World2!" />
            <ForceSuccess name="Force Success">
                <Echo name="Echo 3" message="Hello, World3!" />
            </ForceSuccess>
        </Sequence>
    """
    bt_factory = BehaviorTreeFactory()
    bt = bt_factory.build_tree(xml_string)
    bt.tick_while_running()
    assert bt.root.status == Status.SUCCESS
    assert bt.root.children[0].status is None
    assert bt.root.children[1].status is None
    assert bt.root.children[2].status is None


def test_selector_node1():
    xml_string = """
        <Selector>
            <ForceFailure name="Force Failure">
                <Echo name="Echo 1" message="Hello, World1!" />
            </ForceFailure>
            <Echo name="Echo 2" message="Hello, World2!" />
            <Echo name="Echo 3" message="Hello, World3!" />
        </Selector>
    """
    bt_factory = BehaviorTreeFactory()
    bt = bt_factory.build_tree(xml_string)
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status == Status.FAILURE
    assert bt.root.children[1].status is None
    assert bt.root.children[2].status is None
    bt.tick()
    assert bt.root.status == Status.SUCCESS
    assert bt.root.children[0].status is None
    assert bt.root.children[1].status is None
    assert bt.root.children[2].status is None


def test_selector_node2():
    xml_string = """
        <Selector>
            <ForceFailure name="Force Success">
                <Echo name="Echo 1" message="Hello, World1!" />
            </ForceFailure>
            <ForceFailure name="Force Failure">
                <Echo name="Echo 2" message="Hello, World2!" />
            </ForceFailure>
        </Selector>
    """
    bt_factory = BehaviorTreeFactory()
    bt = bt_factory.build_tree(xml_string)
    bt.tick_while_running()
    assert bt.root.status == Status.FAILURE
    assert bt.root.children[0].status is None
    assert bt.root.children[1].status is None


def test_while_do_else_node():
    xml_string = """
        <WhileDoElse>
            <Count name="Count" count_threshold="3" />
            <Echo name="Echo 1" message="Hello, World1!" />
            <Echo name="Echo 2" message="Hello, World2!" />
        </WhileDoElse>
    """

    class CountNode(ActionNode):
        def __init__(self, name, count_threshold):
            super().__init__(name)
            self.count = 0
            self.count_threshold = count_threshold

        def tick(self):
            self.count += 1
            if self.count >= self.count_threshold:
                return Status.FAILURE
            else:
                return Status.SUCCESS

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "Count",
        lambda node: CountNode(
            node.attrib.get("name", CountNode.__name__),
            int(node.attrib["count_threshold"]),
        ),
    )
    bt = bt_factory.build_tree(xml_string)
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status == Status.SUCCESS
    assert bt.root.children[1].status is Status.SUCCESS
    assert bt.root.children[2].status is None
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status == Status.SUCCESS
    assert bt.root.children[1].status is Status.SUCCESS
    assert bt.root.children[2].status is None
    bt.tick()
    assert bt.root.status == Status.SUCCESS
    assert bt.root.children[0].status is None
    assert bt.root.children[1].status is None
    assert bt.root.children[2].status is None


def test_node_children():
    # ControlNode Must have children
    xml_string = """
        <Sequence>
        </Sequence>
    """
    bt_factory = BehaviorTreeFactory()
    with pytest.raises(ValueError):
        bt_factory.build_tree(xml_string)

    # DecoratorNode Must have child
    xml_string = """
        <Inverter>
        </Inverter>
    """
    with pytest.raises(ValueError):
        bt_factory.build_tree(xml_string)

    # DecoratorNode Must have only one child
    xml_string = """
        <Inverter>
            <Echo name="Echo 1" message="Hello, World1!" />
            <Echo name="Echo 2" message="Hello, World2!" />
        </Inverter>
    """
    with pytest.raises(ValueError):
        bt_factory.build_tree(xml_string)

    # ActionNode Must have no children
    xml_string = """
        <Echo name="Echo 1" message="Hello, World1!">
            <Echo name="Echo 2" message="Hello, World2!" />
        </Echo>
    """
    with pytest.raises(ValueError):
        bt_factory.build_tree(xml_string)

    # WhileDoElse Must have exactly 2 or 3 children
    xml_string = """
        <WhileDoElse>
            <Echo name="Echo 1" message="Hello, World1!" />
        </WhileDoElse>
    """
    with pytest.raises(ValueError):
        bt = bt_factory.build_tree(xml_string)
        bt.tick()

    xml_string = """
        <WhileDoElse>
            <Echo name="Echo 1" message="Hello, World1!" />
            <Echo name="Echo 2" message="Hello, World2!" />
            <Echo name="Echo 3" message="Hello, World3!" />
            <Echo name="Echo 4" message="Hello, World4!" />
        </WhileDoElse>
    """
    with pytest.raises(ValueError):
        bt = bt_factory.build_tree(xml_string)
        bt.tick()


def test_retry_until_successful_success():
    """Test RetryUntilSuccessful node where child eventually succeeds."""
    class SuccessAfterNNode(ActionNode):
        def __init__(self, name, n):
            super().__init__(name)
            self.count = 0
            self.n = n

        def tick(self):
            self.count += 1
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

    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.child.status == Status.FAILURE
    assert bt.root.current_attempt == 1

    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.child.status == Status.FAILURE
    assert bt.root.current_attempt == 2

    bt.tick()
    assert bt.root.status == Status.SUCCESS
    assert bt.root.child.status == Status.SUCCESS
    assert bt.root.current_attempt == 2


def test_retry_until_successful_failure():
    """Test RetryUntilSuccessful node where child always fails."""
    class AlwaysFailNode(ActionNode):
        def __init__(self, name):
            super().__init__(name)
            self.tick_count = 0

        def tick(self):
            self.tick_count += 1
            return Status.FAILURE

    xml_string = """
        <RetryUntilSuccessful num_attempts="3">
            <AlwaysFail name="Test" />
        </RetryUntilSuccessful>
    """

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "AlwaysFail",
        lambda node: AlwaysFailNode(
            node.attrib.get("name", AlwaysFailNode.__name__),
        ),
    )
    bt = bt_factory.build_tree(xml_string)

    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.current_attempt == 1

    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.current_attempt == 2

    bt.tick()
    assert bt.root.status == Status.FAILURE
    assert bt.root.current_attempt == 3
    assert bt.root.child.tick_count == 3


def test_retry_until_successful_running_passthrough():
    """Test RetryUntilSuccessful node passes through RUNNING status."""
    class RunningNode(ActionNode):
        def __init__(self, name):
            super().__init__(name)
            self.tick_count = 0

        def tick(self):
            self.tick_count += 1
            if self.tick_count < 3:
                return Status.RUNNING
            return Status.SUCCESS

    xml_string = """
        <RetryUntilSuccessful num_attempts="5">
            <RunningAction name="Test" />
        </RetryUntilSuccessful>
    """

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "RunningAction",
        lambda node: RunningNode(
            node.attrib.get("name", RunningNode.__name__),
        ),
    )
    bt = bt_factory.build_tree(xml_string)

    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.child.status == Status.RUNNING
    assert bt.root.current_attempt == 0

    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.child.status == Status.RUNNING
    assert bt.root.current_attempt == 0

    bt.tick()
    assert bt.root.status == Status.SUCCESS
    assert bt.root.child.status == Status.SUCCESS
    assert bt.root.current_attempt == 0


def test_retry_until_successful_reset():
    """Test RetryUntilSuccessful node reset behavior with other nodes."""
    class SuccessAfterNNode(ActionNode):
        def __init__(self, name, n):
            super().__init__(name)
            self.count = 0
            self.n = n

        def tick(self):
            self.count += 1
            if self.count >= self.n:
                return Status.SUCCESS
            else:
                return Status.FAILURE

    xml_string = """
        <Sequence>
            <RetryUntilSuccessful name="Retry" num_attempts="3">
                <SuccessAfterN name="Test" n="2" />
            </RetryUntilSuccessful>
            <Echo name="Done" message="Done!" />
        </Sequence>
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

    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status == Status.RUNNING
    assert bt.root.children[0].current_attempt == 1

    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status == Status.SUCCESS
    assert bt.root.children[0].current_attempt == 1

    bt.tick()
    assert bt.root.status == Status.SUCCESS

    bt.reset()
    assert bt.root.status is None
    assert bt.root.children[0].status is None
    assert bt.root.children[0].current_attempt == 0
    assert bt.root.children[0].child.status is None
    assert bt.root.children[0].child.count == 0


if __name__ == "__main__":
    conftest.run_this_test(__file__)
