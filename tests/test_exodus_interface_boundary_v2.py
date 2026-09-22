from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "docs/exodus/CHATGPT_EXODUS_INTERFACE_BOUNDARY_V2.md"


def test_current_exodus_boundary_makes_chats_terminals_not_state_containers():
    text = BOUNDARY.read_text(encoding="utf-8").lower()
    assert "execution interfaces/terminals" in text
    assert "training_chat != durable_capability_container" in text
    assert "working_chat != durable_identity" in text
    assert "chat_branch != authority_source" in text
    assert "conversation_history != current_control_state" in text


def test_persistent_human_interface_topology_is_explicit_without_worker_chat_dependency():
    text = BOUNDARY.read_text(encoding="utf-8")
    for name in ("Vera", "Vera Control Plane Coordinator", "BT2 Coordinator"):
        assert name in text
    lowered = text.lower()
    assert "role may execute through a temporary terminal" in lowered
    assert "permanent-chat requirements" in lowered


def test_default_vera_training_docs_are_marked_historical_for_runtime_continuity():
    for relative in (
        "template/default-vera-v1/CONTINUITY.md",
        "template/default-vera-v1/OPERATOR_QUICKSTART_V1.md",
        "template/default-vera-v1/README.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8").lower()
        assert text.startswith("> **current exodus boundary:**")
        assert "historical" in text
        assert "chatgpt_exodus_interface_boundary_v2.md" in text


def test_current_workstream_protocol_is_the_coordination_owner():
    text = (ROOT / "docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V2.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "v2 supersedes v1" in text
    assert "current nonproduction workstream coordination protocol" in text
