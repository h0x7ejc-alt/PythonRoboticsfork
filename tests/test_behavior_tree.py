import pytest
import conftest

from MissionPlanning.BehaviorTree.behavior_tree import (
    BehaviorTreeFactory,
    Status,
    ActionNode,
    RetryUntilSuccessfulNode,
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


def test_retry_until_successful_success_first_try():
    class SucceedOnNthTryNode(ActionNode):
        def __init__(self, name, n):
            super().__init__(name)
            self.n = n
            self.count = 0

        def tick(self):
            self.count += 1
            if self.count >= self.n:
                return Status.SUCCESS
            return Status.FAILURE

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "SucceedOnNth",
        lambda node: SucceedOnNthTryNode(
            node.attrib.get("name", "SucceedOnNth"),
            int(node.attrib["n"]),
        ),
    )
    xml_string = """
        <RetryUntilSuccessful num_attempts="3">
            <SucceedOnNth name="SucceedOn3rd" n="1" />
        </RetryUntilSuccessful>
    """
    bt = bt_factory.build_tree(xml_string)
    bt.tick()
    assert bt.root.status == Status.SUCCESS
    assert bt.root.child.status == Status.SUCCESS
    assert bt.root.current_attempt == 0


def test_retry_until_successful_retry_then_success():
    class SucceedOnNthTryNode(ActionNode):
        def __init__(self, name, n):
            super().__init__(name)
            self.n = n
            self.count = 0

        def tick(self):
            self.count += 1
            if self.count >= self.n:
                return Status.SUCCESS
            return Status.FAILURE

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "SucceedOnNth",
        lambda node: SucceedOnNthTryNode(
            node.attrib.get("name", "SucceedOnNth"),
            int(node.attrib["n"]),
        ),
    )
    xml_string = """
        <RetryUntilSuccessful num_attempts="3">
            <SucceedOnNth name="SucceedOn3rd" n="3" />
        </RetryUntilSuccessful>
    """
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
    assert bt.root.current_attempt == 0


def test_retry_until_successful_exhausted_attempts():
    class AlwaysFailureNode(ActionNode):
        def __init__(self, name):
            super().__init__(name)

        def tick(self):
            return Status.FAILURE

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "AlwaysFailure",
        lambda node: AlwaysFailureNode(
            node.attrib.get("name", "AlwaysFailure"),
        ),
    )
    xml_string = """
        <RetryUntilSuccessful num_attempts="3">
            <AlwaysFailure name="AlwaysFails" />
        </RetryUntilSuccessful>
    """
    bt = bt_factory.build_tree(xml_string)
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.current_attempt == 1
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.current_attempt == 2
    bt.tick()
    assert bt.root.status == Status.FAILURE
    assert bt.root.current_attempt == 0


def test_retry_until_successful_running_pass_through():
    class RunningNode(ActionNode):
        def __init__(self, name):
            super().__init__(name)

        def tick(self):
            return Status.RUNNING

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "Running",
        lambda node: RunningNode(
            node.attrib.get("name", "Running"),
        ),
    )
    xml_string = """
        <RetryUntilSuccessful num_attempts="3">
            <Running name="KeepsRunning" />
        </RetryUntilSuccessful>
    """
    bt = bt_factory.build_tree(xml_string)
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.child.status == Status.RUNNING
    assert bt.root.current_attempt == 0
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.child.status == Status.RUNNING
    assert bt.root.current_attempt == 0


def test_retry_until_successful_reset_behavior():
    class SucceedOnNthTryNode(ActionNode):
        def __init__(self, name, n):
            super().__init__(name)
            self.n = n
            self.count = 0

        def tick(self):
            self.count += 1
            if self.count >= self.n:
                return Status.SUCCESS
            return Status.FAILURE

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "SucceedOnNth",
        lambda node: SucceedOnNthTryNode(
            node.attrib.get("name", "SucceedOnNth"),
            int(node.attrib["n"]),
        ),
    )
    xml_string = """
        <RetryUntilSuccessful num_attempts="3">
            <SucceedOnNth name="SucceedOn3rd" n="3" />
        </RetryUntilSuccessful>
    """
    bt = bt_factory.build_tree(xml_string)
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.current_attempt == 1
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.current_attempt == 2
    bt.reset()
    assert bt.root.current_attempt == 0
    assert bt.root.child.status is None
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.current_attempt == 1


def test_retry_until_successful_combined_with_sequence():
    class SucceedOnNthTryNode(ActionNode):
        def __init__(self, name, n):
            super().__init__(name)
            self.n = n
            self.count = 0

        def tick(self):
            self.count += 1
            if self.count >= self.n:
                return Status.SUCCESS
            return Status.FAILURE

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder(
        "SucceedOnNth",
        lambda node: SucceedOnNthTryNode(
            node.attrib.get("name", "SucceedOnNth"),
            int(node.attrib["n"]),
        ),
    )
    xml_string = """
        <Sequence>
            <Echo name="Setup" message="setup" />
            <RetryUntilSuccessful num_attempts="3">
                <SucceedOnNth name="MayFail" n="2" />
            </RetryUntilSuccessful>
            <Echo name="Cleanup" message="cleanup" />
        </Sequence>
    """
    bt = bt_factory.build_tree(xml_string)
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status == Status.SUCCESS
    assert bt.root.children[1].status == Status.RUNNING
    assert bt.root.children[1].child.status == Status.FAILURE
    assert bt.root.children[1].current_attempt == 1
    assert bt.root.children[2].status is None
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status is None
    assert bt.root.children[1].status == Status.SUCCESS
    assert bt.root.children[1].child.status == Status.SUCCESS
    assert bt.root.children[1].current_attempt == 0
    assert bt.root.children[2].status == Status.SUCCESS


if __name__ == "__main__":
    conftest.run_this_test(__file__)
