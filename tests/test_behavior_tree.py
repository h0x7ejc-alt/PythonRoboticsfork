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
    external_state = {"fails_left": 2}
    xml_string = """
        <RetryUntilSuccessful num_attempts="3">
            <ExternalFail name="ExternalFail" />
        </RetryUntilSuccessful>
    """

    class ExternalFailNode(ActionNode):
        def tick(self):
            if external_state["fails_left"] > 0:
                external_state["fails_left"] -= 1
                return Status.FAILURE
            return Status.SUCCESS

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder("ExternalFail", lambda node: ExternalFailNode(node.attrib.get("name")))
    bt = bt_factory.build_tree(xml_string)

    # Tick 1: fails, attempts=1. Returns RUNNING.
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.attempts == 1

    # Tick 2: fails, attempts=2. Returns RUNNING.
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.attempts == 2

    # Tick 3: succeeds. Returns SUCCESS.
    bt.tick()
    assert bt.root.status == Status.SUCCESS
    assert bt.root.attempts == 2


def test_retry_until_successful_failure():
    external_state = {"fails_left": 3}
    xml_string = """
        <RetryUntilSuccessful num_attempts="3">
            <ExternalFail name="ExternalFail" />
        </RetryUntilSuccessful>
    """

    class ExternalFailNode(ActionNode):
        def tick(self):
            if external_state["fails_left"] > 0:
                external_state["fails_left"] -= 1
                return Status.FAILURE
            return Status.SUCCESS

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder("ExternalFail", lambda node: ExternalFailNode(node.attrib.get("name")))
    bt = bt_factory.build_tree(xml_string)

    # Tick 1: fails, attempts=1. Returns RUNNING.
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.attempts == 1

    # Tick 2: fails, attempts=2. Returns RUNNING.
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.attempts == 2

    # Tick 3: fails, attempts=3. limit reached, Returns FAILURE.
    bt.tick()
    assert bt.root.status == Status.FAILURE
    assert bt.root.attempts == 3


def test_retry_until_successful_running():
    xml_string = """
        <RetryUntilSuccessful num_attempts="3">
            <RunningNode name="Running" />
        </RetryUntilSuccessful>
    """

    class RunningNode(ActionNode):
        def tick(self):
            return Status.RUNNING

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder("RunningNode", lambda node: RunningNode(node.attrib.get("name")))
    bt = bt_factory.build_tree(xml_string)

    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.attempts == 0


def test_retry_until_successful_reset():
    external_state = {"fails_left": 1}
    xml_string = """
        <Sequence>
            <RetryUntilSuccessful num_attempts="3">
                <ExternalFail name="ExternalFail" />
            </RetryUntilSuccessful>
            <ForceFailure name="ForceFail">
                <Echo name="Echo" message="test" />
            </ForceFailure>
        </Sequence>
    """

    class ExternalFailNode(ActionNode):
        def tick(self):
            if external_state["fails_left"] > 0:
                external_state["fails_left"] -= 1
                return Status.FAILURE
            return Status.SUCCESS

    bt_factory = BehaviorTreeFactory()
    bt_factory.register_node_builder("ExternalFail", lambda node: ExternalFailNode(node.attrib.get("name")))
    bt = bt_factory.build_tree(xml_string)

    # Tick 1: Retry child fails, attempts=1. Sequence gets RUNNING.
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status == Status.RUNNING
    assert bt.root.children[0].attempts == 1

    # Tick 2: Retry child succeeds. Retry returns SUCCESS. Sequence gets RUNNING.
    bt.tick()
    assert bt.root.status == Status.RUNNING
    assert bt.root.children[0].status == Status.SUCCESS

    # Tick 3: Sequence ticks ForceFailure. It fails. Sequence returns FAILURE and resets children.
    bt.tick()
    assert bt.root.status == Status.FAILURE
    assert bt.root.children[0].status is None
    assert bt.root.children[0].attempts == 0


if __name__ == "__main__":
    conftest.run_this_test(__file__)
