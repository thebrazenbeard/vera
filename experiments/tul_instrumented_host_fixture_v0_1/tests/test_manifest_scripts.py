from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


GENERATOR_SOURCE = (
    Path(__file__).resolve().parents[1] / "scripts" / "generate_manifest.py"
)
VERIFIER_SOURCE = (
    Path(__file__).resolve().parents[1] / "scripts" / "verify_manifest.py"
)


def _build_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    repository = tmp_path / "repository"
    experiment = repository / "experiments" / "tul_instrumented_host_fixture_v0_1"
    scripts = experiment / "scripts"
    source = repository / "src" / "tul_fixture"
    scripts.mkdir(parents=True)
    source.mkdir(parents=True)

    generator = scripts / "generate_manifest.py"
    verifier = scripts / "verify_manifest.py"
    generator.write_bytes(GENERATOR_SOURCE.read_bytes())
    verifier.write_bytes(VERIFIER_SOURCE.read_bytes())

    (experiment / "README.md").write_text("fixture\n", encoding="utf-8")
    (source / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    return repository, generator, verifier


def _run(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=script.parents[1],
        text=True,
        capture_output=True,
        check=False,
    )


def test_generator_and_verifier_cover_complete_reproducible_boundary(tmp_path):
    repository, generator, verifier = _build_fixture(tmp_path)
    experiment = generator.parents[1]

    transient = experiment / ".pytest_cache" / "ignored.txt"
    transient.parent.mkdir()
    transient.write_text("ignore me\n", encoding="utf-8")
    (repository / "src" / "tul_fixture" / "module.pyc").write_bytes(b"ignored")

    symlink = experiment / "linked.txt"
    try:
        os.symlink(experiment / "README.md", symlink)
    except (OSError, NotImplementedError):
        symlink = None

    generated = _run(generator)
    assert generated.returncode == 0, generated.stderr

    manifest = experiment / "SHA256SUMS.txt"
    entries = manifest.read_text(encoding="utf-8").splitlines()
    assert any(line.endswith("  experiments/tul_instrumented_host_fixture_v0_1/README.md") for line in entries)
    assert any(line.endswith("  src/tul_fixture/core.py") for line in entries)
    assert not any(".pytest_cache" in line for line in entries)
    assert not any(line.endswith(".pyc") for line in entries)
    if symlink is not None:
        assert not any(line.endswith("linked.txt") for line in entries)

    verified = _run(verifier)
    assert verified.returncode == 0, verified.stderr
    assert "complete boundary coverage" in verified.stdout


def test_verifier_rejects_unlisted_source_file(tmp_path):
    repository, generator, verifier = _build_fixture(tmp_path)
    assert _run(generator).returncode == 0

    (repository / "src" / "tul_fixture" / "added_later.py").write_text(
        "VALUE = 2\n", encoding="utf-8"
    )

    verified = _run(verifier)
    assert verified.returncode != 0
    assert "unlisted: src/tul_fixture/added_later.py" in verified.stderr


def test_verifier_rejects_duplicate_and_traversal_entries(tmp_path):
    _, generator, verifier = _build_fixture(tmp_path)
    assert _run(generator).returncode == 0

    manifest = generator.parents[1] / "SHA256SUMS.txt"
    first_line = manifest.read_text(encoding="utf-8").splitlines()[0]
    digest = first_line.split("  ", 1)[0]
    manifest.write_text(
        first_line + "\n" + first_line + "\n" + f"{digest}  ../escape\n",
        encoding="utf-8",
    )

    verified = _run(verifier)
    assert verified.returncode != 0
    assert "duplicate entry:" in verified.stderr
    assert "invalid path on line 3" in verified.stderr
