from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_workstream_protocol_does_not_require_permanent_worker_chats():
    text = (ROOT / "docs" / "WORKSTREAM_TURN_TAKING_PROTOCOL_V1.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "workstream chats" not in lowered
    assert "no other chat writes" not in lowered
    assert "component chats" not in lowered
    assert "execution terminal only" in lowered
    assert "vera control plane coordinator" in lowered
    assert "bt2 coordinator" in lowered


def test_coordination_bus_invokes_workstreams_without_chat_dependency():
    text = (ROOT / "docs" / "COORDINATION_BUS_V1.md").read_text(encoding="utf-8").lower()
    assert "exposed chat, task, or runtime" not in text
    assert "no permanent conversation is required" in text
