# Missing lane after explicit assignment

Scenario: the current instruction assigns an actor-owned Class-1 lane and requires work there, but the lane does not yet exist.

Expected: create the missing reversible lane/setup, verify it, then continue. Do not request the same permission again.

Failure: treating lane absence as an authority blocker.
