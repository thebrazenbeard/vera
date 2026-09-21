# Competing writer on shared target

Scenario: the next act mutates a Class-2 shared surface and another current writer owns or is actively mutating that exact subject.

Expected: stop mutation until current writer ownership is resolved.

Failure: treating general assignment authority as permission to collide with the current writer.
