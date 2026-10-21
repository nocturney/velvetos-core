#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from unique_yaml import UniqueYamlError, load_yaml, load_yaml_node
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
MARKER = "VELVET_MACHINE_WRITER_ALLOW:"
PRECHECK_HELPER = "scripts/push-main-with-check-all.sh"
NON_MAIN_LITERAL_PUSHES = ("HEAD:publish-bridge",)


def fail(msg: str) -> None:
    print("FAIL " + msg, file=sys.stderr)
    raise SystemExit(1)


def is_machine_writer(text: str) -> bool:
    if PRECHECK_HELPER in text:
        return True
    if not re.search(r"(?m)^\s*git\s+push\b", text):
        return False
    if "branches: [fix/close-runtime-corners-20260914]" in text and "workflow_dispatch:" not in text:
        return False
    return True


def has_unprotected_default_push(text: str) -> bool:
    """Return true when a writer can push the checked-out/default ref without the precheck helper."""
    if PRECHECK_HELPER in text:
        return False
    for line in text.splitlines():
        cmd = line.strip()
        if not re.match(r"git\s+push\b", cmd):
            continue
        if any(target in cmd for target in NON_MAIN_LITERAL_PUSHES):
            continue
        return True
    return False


def marker_paths(text: str) -> list[str]:
    m = re.search(r"(?m)^\s*#\s*VELVET_MACHINE_WRITER_ALLOW:\s*(.+?)\s*$", text)
    if not m:
        return []
    return [p for p in m.group(1).split() if p]


def has_write_permission(text: str) -> bool:
    """Accept explicit workflow- or job-level contents: write, never implicit defaults."""
    return bool(re.search(r"(?m)^\s*contents:\s*write\s*(?:#.*)?$", text))


FFMPEG_ZIP_SHA256 = "d760e1b3574402ed18b4865851f87d87e73965a982e6453212df8621fed1c508"
UPLOAD_ARTIFACT = "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9"
CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_PYTHON = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
WINDOWS_ACTIONS = {
    CHECKOUT,
    SETUP_PYTHON,
    UPLOAD_ARTIFACT,
}
# The whole ffmpeg step run body is one canonical string.
# Parsing strips the YAML literal-block indent and keeps U+2028/U+2029/U+0085
# inside the line. Comparison drops one trailing newline and nothing else.
CANONICAL_VERIFIER = "python scripts/verify_ffmpeg_zip_sha256.py --path $zip --expected $expected"
CANONICAL_THROW = 'if ($LASTEXITCODE -ne 0) { throw "ffmpeg zip sha256 mismatch: $expected" }'
FFMPEG_STEP_NAME = "Install hashed sensor lock and pinned ffmpeg"
CANONICAL_FFMPEG_RUN = "\n".join((
    "python -m pip install --disable-pip-version-check --require-hashes -r requirements-sensors.py311.lock",
    f'$expected = "{FFMPEG_ZIP_SHA256}"',
    '$zip = Join-Path $env:RUNNER_TEMP "ffmpeg-7.1.1-full_build.zip"',
    'curl.exe -fsSL -o "$zip" "https://github.com/GyanD/codexffmpeg/releases/download/7.1.1/ffmpeg-7.1.1-full_build.zip"',
    CANONICAL_VERIFIER,
    CANONICAL_THROW,
    '$dest = Join-Path $env:RUNNER_TEMP "ffmpeg"',
    "Expand-Archive -Path $zip -DestinationPath $dest",
    "$bin = Get-ChildItem -Path $dest -Recurse -Filter ffmpeg.exe | Select-Object -First 1",
    'if (-not $bin) { throw "ffmpeg.exe missing from the pinned zip" }',
    "Add-Content -Path $env:GITHUB_PATH -Value $bin.DirectoryName",
))
GAP_PROBLEM = "check-all-windows ffmpeg step run body is not the canonical text"
EXIT_RESET = re.compile(r"\$LASTEXITCODE\s*=\s*0\b")
CANONICAL_FFMPEG_KEYS = frozenset({"name", "shell", "run"})
CANONICAL_FFMPEG_SHELL = "pwsh"
# A step-level key: plain, double-quoted, single-quoted, or an explicit ``?`` key.
_RAW_STEP_KEY = re.compile(
    r"^(?:-\s+)?"
    r"(?:"
    r"(?P<plain>[A-Za-z_][A-Za-z0-9_.-]*)\s*:"
    r"|\"(?P<dquote>(?:\\.|[^\"\\])*)\"\s*:"
    r"|'(?P<squote>(?:''|[^'])*)'\s*:"
    r"|\?\s+(?P<complex>\S(?:.*\S)?)\s*"
    r")"
)
# PyYAML normalizes U+0085 to a line feed. These stay inside a "\n"-split line.
UNICODE_LINE_SEPARATORS = ("\u2028", "\u2029", "\u0085")
RUN_HEADER = re.compile(r"^run:\s*\|([-+]?)\s*(?:#.*)?$")
# Tag and branch refs are refused. This set is the only exception, and it starts empty.
ACTION_REF_ALLOWLIST: frozenset[str] = frozenset()
VERSION_COMMENT = re.compile(
    r"^\s*#\s+(?P<action>\S+/\S+)\s+v(?P<version>\d+\.\d+\.\d+)\s*$"
)
SHA_REF = re.compile(r"^[0-9a-f]{40}$")
DOCKER_DIGEST = re.compile(r"^docker://.+@sha256:[0-9a-f]{64}$")
DOCKER_DIGEST_REF = "docker://alpine@sha256:" + ("ab" * 32)


def previous_nonempty(lines: list[str], index: int) -> str:
    """Return the previous non-empty line. index is the 0-based current line."""
    cursor = index - 1
    while cursor >= 0 and lines[cursor].strip() == "":
        cursor -= 1
    return lines[cursor] if cursor >= 0 else ""


def _pairs(node):
    if not isinstance(node, MappingNode):
        return None
    pairs = []
    for key_node, value_node in node.value:
        if not isinstance(key_node, ScalarNode):
            return "complex-key"
        pairs.append((key_node.value, value_node))
    return pairs


def _docker_digest_ok(spec: str) -> bool:
    return DOCKER_DIGEST.fullmatch(spec) is not None


def _classify_uses(spec, line_no, lines, path, problems, allowed) -> None:
    if spec.startswith("./"):
        return
    if spec.startswith("docker://"):
        if _docker_digest_ok(spec):
            return
        problems.append(f"{path}:{line_no}: docker ref is not a sha256 digest: {spec}")
        return
    if "@" not in spec:
        problems.append(f"{path}:{line_no}: action ref has no pin: {spec}")
        return
    action, ref = spec.rsplit("@", 1)
    if spec in allowed:
        return
    if not SHA_REF.fullmatch(ref):
        problems.append(f"{path}:{line_no}: tag or branch ref is not allowlisted: {spec}")
        return
    comment = VERSION_COMMENT.match(previous_nonempty(lines, line_no - 1))
    if comment is None:
        problems.append(f"{path}:{line_no}: SHA pin missing version comment: {spec}")
        return
    commented = comment.group("action")
    if action != commented and not action.startswith(commented + "/"):
        problems.append(f"{path}:{line_no}: version comment {commented} does not match {action}")


def _append_uses(value_node, lines, path, problems, allowed) -> None:
    line_no = value_node.start_mark.line + 1 if value_node.start_mark else 0
    if not isinstance(value_node, ScalarNode) or value_node.tag == "tag:yaml.org,2002:null":
        problems.append(f"{path}:{line_no}: uses must be a string")
        return
    _classify_uses(value_node.value.strip(), line_no, lines, path, problems, allowed)


def _walk_steps(node, lines, path, problems, allowed) -> None:
    if not isinstance(node, SequenceNode):
        problems.append(f"{path}: steps must be a sequence")
        return
    for step in node.value:
        if not isinstance(step, MappingNode):
            line_no = step.start_mark.line + 1 if step.start_mark else 0
            problems.append(f"{path}:{line_no}: step must be a mapping")
            continue
        pairs = _pairs(step)
        if pairs == "complex-key":
            problems.append(f"{path}: complex mapping key refused")
            continue
        for key, value in pairs:
            if key == "uses":
                _append_uses(value, lines, path, problems, allowed)


def _walk_job(node, lines, path, problems, allowed) -> None:
    if not isinstance(node, MappingNode):
        problems.append(f"{path}: job must be a mapping")
        return
    pairs = _pairs(node)
    if pairs == "complex-key":
        problems.append(f"{path}: complex mapping key refused")
        return
    for key, value in pairs:
        if key == "uses":
            _append_uses(value, lines, path, problems, allowed)
        elif key == "steps":
            _walk_steps(value, lines, path, problems, allowed)


def _walk_jobs(node, lines, path, problems, allowed) -> None:
    if not isinstance(node, MappingNode):
        problems.append(f"{path}: jobs must be a mapping")
        return
    pairs = _pairs(node)
    if pairs == "complex-key":
        problems.append(f"{path}: complex mapping key refused")
        return
    for _job_id, job in pairs:
        _walk_job(job, lines, path, problems, allowed)


def _walk_runs(node, lines, path, problems, allowed) -> None:
    if not isinstance(node, MappingNode):
        return
    pairs = _pairs(node)
    if not isinstance(pairs, list):
        return
    for key, value in pairs:
        if key == "steps":
            _walk_steps(value, lines, path, problems, allowed)


def _walk_document(node, lines, path, problems, allowed) -> None:
    if not isinstance(node, MappingNode):
        problems.append(f"{path}: workflow document must be a mapping")
        return
    pairs = _pairs(node)
    if pairs == "complex-key":
        problems.append(f"{path}: complex mapping key refused")
        return
    for key, value in pairs:
        if key == "jobs":
            _walk_jobs(value, lines, path, problems, allowed)
        elif key == "steps":
            _walk_steps(value, lines, path, problems, allowed)
        elif key == "runs":
            _walk_runs(value, lines, path, problems, allowed)


_PIN_REFUSAL = {
    "duplicate": "duplicate key",
    "anchor": "anchor refused",
    "alias": "alias refused",
    "merge": "merge key refused",
    "complex": "complex mapping key refused",
    "syntax": "YAML refused",
}


def action_pin_problems(
    text: str,
    *,
    path: str = "<fixture>",
    allowlist: frozenset[str] | None = None,
) -> list[str]:
    """Every remote uses is a 40-hex SHA plus a version comment, unless allowlisted.

    docker:// refs must be docker://...@sha256: and 64 lowercase hex. Local ./ refs
    stay local. ``scripts/unique_yaml.py`` loads the document: a duplicate key, an
    anchor, an alias, a merge key, and an explicit ``?`` key are refused anywhere
    in the file.
    """
    allowed = ACTION_REF_ALLOWLIST if allowlist is None else allowlist
    try:
        node = load_yaml_node(text)
    except UniqueYamlError as exc:
        phrase = _PIN_REFUSAL.get(exc.kind, exc.kind)
        return [f"{path}: {phrase}: {exc}"]
    if node is None:
        return []
    problems: list[str] = []
    _walk_document(node, text.splitlines(), path, problems, allowed)
    return problems


def discover_pin_paths(root: Path) -> list[Path]:
    """Workflow files plus in-repo composite action.yml files under .github/."""
    paths: list[Path] = []
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        paths.extend(workflows.glob("*.yml"))
        paths.extend(workflows.glob("*.yaml"))
    github = root / ".github"
    if github.is_dir():
        paths.extend(github.rglob("action.yml"))
        paths.extend(github.rglob("action.yaml"))
    return sorted(set(paths))


def scan_pin_paths(paths: list[Path]) -> list[str]:
    problems: list[str] = []
    for path in paths:
        problems.extend(
            action_pin_problems(path.read_text(encoding="utf-8"), path=path.as_posix())
        )
    return problems


def _require(problems: list[str], needle: str, label: str) -> None:
    if not any(needle in problem for problem in problems):
        fail(label + " was not refused: " + "; ".join(problems))


def _require_clean(problems: list[str], label: str) -> None:
    if problems:
        fail(label + " was refused: " + "; ".join(problems))


def prove_workflow_action_pins(core_workflow: str) -> str:
    """Fixtures plus mutations that revert the Linux and Windows checkouts to @v7."""
    if ACTION_REF_ALLOWLIST:
        fail("workflow action ref allowlist must start empty")
    tag_fixture = "steps:\n  - uses: actions/checkout@v7\n"
    _require(action_pin_problems(tag_fixture), "not allowlisted", "@v7 fixture")
    branch_fixture = "steps:\n  - uses: actions/checkout@main\n"
    _require(action_pin_problems(branch_fixture), "not allowlisted", "branch ref fixture")
    pinned_fixture = (
        "steps:\n"
        "  # actions/checkout v7.0.1\n"
        "  - uses: " + CHECKOUT + "\n"
    )
    _require_clean(action_pin_problems(pinned_fixture), "pinned SHA fixture")
    bare_sha = "steps:\n  - uses: " + CHECKOUT + "\n"
    _require(action_pin_problems(bare_sha), "missing version comment", "bare SHA")
    if action_pin_problems(tag_fixture, allowlist=frozenset({"actions/checkout@v7"})):
        fail("explicit allowlist did not accept actions/checkout@v7")
    flow_bad = "steps:\n  - { name: Sneaky, uses: actions/checkout@v7 }\n"
    _require(action_pin_problems(flow_bad), "not allowlisted", "flow-style uses")
    flow_ok = (
        "steps:\n"
        "  # actions/checkout v7.0.1\n"
        "  - { name: Sneaky, uses: " + CHECKOUT + " }\n"
    )
    _require_clean(action_pin_problems(flow_ok), "flow-style SHA pin")
    docker_latest = "steps:\n  - uses: docker://alpine:latest\n"
    _require(action_pin_problems(docker_latest), "sha256 digest", "docker://alpine:latest")
    if not action_pin_problems(docker_latest, allowlist=frozenset({"docker://alpine:latest"})):
        fail("allowlist accepted docker://alpine:latest")
    _require_clean(
        action_pin_problems("steps:\n  - uses: " + DOCKER_DIGEST_REF + "\n"),
        "docker digest",
    )
    tagged_digest = "docker://alpine:3.20@sha256:" + ("cd" * 32)
    _require_clean(
        action_pin_problems("steps:\n  - uses: " + tagged_digest + "\n"),
        "docker tag-and-digest",
    )
    _require(
        action_pin_problems("steps:\n  - uses: docker://alpine@sha256:abcd\n"),
        "sha256 digest",
        "short docker digest",
    )
    _require(
        action_pin_problems("steps:\n  - uses: docker://alpine@sha256:" + ("AB" * 32) + "\n"),
        "sha256 digest",
        "uppercase docker digest",
    )
    _require_clean(
        action_pin_problems("steps:\n  - uses: ./.github/actions/local\n"),
        "local action",
    )
    duplicate = (
        "steps:\n"
        "  - name: one\n"
        "    name: two\n"
        "    # actions/checkout v7.0.1\n"
        "    uses: " + CHECKOUT + "\n"
    )
    _require(action_pin_problems(duplicate), "duplicate key", "duplicate key")
    hidden_tag = (
        "steps:\n"
        "  # actions/checkout v7.0.1\n"
        "  - uses: actions/checkout@v7\n"
        "    # actions/checkout v7.0.1\n"
        "    uses: " + CHECKOUT + "\n"
    )
    _require(action_pin_problems(hidden_tag), "duplicate key", "duplicate uses")
    anchored = (
        "steps:\n"
        "  - &sneaky\n"
        "    # actions/checkout v7.0.1\n"
        "    uses: " + CHECKOUT + "\n"
    )
    _require(action_pin_problems(anchored), "anchor refused", "step anchor")
    aliased = (
        "x-base: &base\n"
        "  # actions/checkout v7.0.1\n"
        "  uses: " + CHECKOUT + "\n"
        "steps:\n"
        "  - *base\n"
    )
    _require(action_pin_problems(aliased), "anchor refused", "anchor feeding a step alias")
    bare_alias = "steps:\n  - *base\n"
    _require(action_pin_problems(bare_alias), "alias refused", "step alias")
    merged = (
        "steps:\n"
        "  - <<:\n"
        "      # actions/checkout v7.0.1\n"
        "      uses: " + CHECKOUT + "\n"
        "    name: kept\n"
    )
    _require(action_pin_problems(merged), "merge key refused", "step merge key")
    reusable = (
        "jobs:\n"
        "  call:\n"
        "    uses: org/repo/.github/workflows/ci.yml@v1\n"
    )
    _require(action_pin_problems(reusable), "not allowlisted", "reusable workflow uses")
    reusable_ok = (
        "jobs:\n"
        "  call:\n"
        "    # org/repo v1.2.3\n"
        "    uses: org/repo/.github/workflows/ci.yml@" + ("a" * 40) + "\n"
    )
    _require_clean(action_pin_problems(reusable_ok), "pinned reusable workflow")
    job_alias = "jobs:\n  call: *job\n"
    _require(action_pin_problems(job_alias), "alias refused", "job alias")
    composite = (
        "name: sneaky\n"
        "runs:\n"
        "  using: composite\n"
        "  steps:\n"
        "    - uses: actions/checkout@v7\n"
    )
    _require(action_pin_problems(composite), "not allowlisted", "composite action uses")
    composite_ok = (
        "name: local\n"
        "runs:\n"
        "  using: composite\n"
        "  steps:\n"
        "    # actions/checkout v7.0.1\n"
        "    - uses: " + CHECKOUT + "\n"
    )
    _require_clean(action_pin_problems(composite_ok), "pinned composite action")
    unknown_tag = "steps:\n  - uses: !localtag actions/checkout@v7\n"
    _require(action_pin_problems(unknown_tag), "YAML refused", "unknown YAML tag")
    injected = core_workflow.replace(
        "      - uses: " + CHECKOUT,
        "      - { name: Sneaky, uses: actions/checkout@v7 }\n      - uses: " + CHECKOUT,
        1,
    )
    _require(
        action_pin_problems(injected, path=".github/workflows/check-all.yml"),
        "not allowlisted",
        "flow-style uses injected into check-all.yml",
    )
    docker_injected = core_workflow.replace(
        "      - uses: " + CHECKOUT,
        "      - uses: docker://alpine:latest\n      - uses: " + CHECKOUT,
        1,
    )
    _require(
        action_pin_problems(docker_injected, path=".github/workflows/check-all.yml"),
        "sha256 digest",
        "docker://alpine:latest injected into check-all.yml",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workflow = root / ".github" / "workflows"
        action = root / ".github" / "actions" / "sneaky"
        workflow.mkdir(parents=True)
        action.mkdir(parents=True)
        (workflow / "flow.yml").write_text(flow_bad, encoding="utf-8")
        (action / "action.yml").write_text(composite, encoding="utf-8")
        discovered = discover_pin_paths(root)
        if workflow / "flow.yml" not in discovered or action / "action.yml" not in discovered:
            fail("pin discovery missed a workflow or composite action")
        discovered_problems = scan_pin_paths(discovered)
        _require(discovered_problems, "not allowlisted", "discovered flow or composite uses")
        if sum("not allowlisted" in problem for problem in discovered_problems) < 2:
            fail("discovery scan did not refuse both the flow workflow and the composite action")
    linux_reverted = core_workflow.replace(CHECKOUT, "actions/checkout@v7", 1)
    if "  check-all-windows:" not in linux_reverted:
        fail("linux pin mutation lost the windows job")
    windows_of_linux_revert = linux_reverted.split("  check-all-windows:", 1)[1]
    if windows_job_problems(windows_of_linux_revert):
        fail("linux @v7 revert disturbed the windows job sensor")
    if not any(
        "not allowlisted" in problem and "@v7" in problem
        for problem in action_pin_problems(linux_reverted, path=".github/workflows/check-all.yml")
    ):
        fail("reverting the Linux checkout to @v7 was not caught")
    windows_unpinned = core_workflow.split("  check-all-windows:", 1)[1].replace(
        CHECKOUT, "actions/checkout@v7", 1
    )
    if not any(
        "not allowlisted" in problem and "@v7" in problem
        for problem in action_pin_problems(windows_unpinned, path="check-all-windows")
    ):
        fail("reverting the Windows checkout to @v7 was not caught")
    flow_quoted = 'steps:\n  - { "uses": "actions/checkout@v7" }\n'
    _require(action_pin_problems(flow_quoted), "not allowlisted", "quoted flow-style uses")
    quoted_block = 'steps:\n  - "uses": actions/checkout@v7\n'
    _require(action_pin_problems(quoted_block), "not allowlisted", "quoted uses key")
    spaced_colon = "steps:\n  - uses : actions/checkout@v7\n"
    _require(action_pin_problems(spaced_colon), "not allowlisted", "space before uses colon")
    multiline_flow = (
        "steps:\n"
        "  - {\n"
        "    name: x,\n"
        "    uses: actions/checkout@v7 }\n"
    )
    _require(action_pin_problems(multiline_flow), "not allowlisted", "multi-line flow uses")
    flow_local = "steps:\n  - { uses: ./.github/actions/local }\n"
    _require_clean(action_pin_problems(flow_local), "local flow action")
    smoke_path = WORKFLOWS / "instagram-read-smoke.yml"
    smoke = smoke_path.read_text(encoding="utf-8")
    _require_clean(action_pin_problems(smoke, path=smoke_path.as_posix()), "instagram-read-smoke.yml")
    smoke_flow = smoke.replace(
        "      - uses: " + CHECKOUT,
        "      - { name: Sneaky, uses: actions/checkout@v7 }\n      - uses: " + CHECKOUT,
        1,
    )
    _require(
        action_pin_problems(smoke_flow, path=smoke_path.as_posix()),
        "not allowlisted",
        "flow-style uses injected into instagram-read-smoke.yml",
    )
    _require(
        action_pin_problems("steps:\n  - uses: docker://alpine\n"),
        "sha256 digest",
        "docker://alpine",
    )
    smoke_docker = smoke.replace(
        "      - uses: " + CHECKOUT,
        "      - uses: docker://alpine:latest\n      - uses: " + CHECKOUT,
        1,
    )
    _require(
        action_pin_problems(smoke_docker, path=smoke_path.as_posix()),
        "sha256 digest",
        "docker://alpine:latest injected into instagram-read-smoke.yml",
    )
    return (
        "tag_fixture=caught sha_fixture=pass bare_sha=caught "
        "linux_revert=caught windows_revert=caught allowlist=empty "
        "flow=caught docker_tag=caught docker_digest=pass duplicate=caught "
        "anchor=caught alias=caught merge=caught reusable=caught composite=caught "
        "quoted_key=caught spaced_colon=caught multiline_flow=caught"
    )


class _PwshScope:
    __slots__ = ("dead", "killed")

    def __init__(self, dead: bool) -> None:
        self.dead = dead
        self.killed = False


def _pwsh_edge(text: str, start: int, end: int) -> bool:
    before = text[start - 1] if start else ""
    after = text[end] if end < len(text) else ""
    return not (before.isalnum() or before in "_$") and not (after.isalnum() or after in "_$")


def _skip_sq(text: str, index: int) -> int:
    cursor = index + 1
    while cursor < len(text):
        if text[cursor] == "'":
            if cursor + 1 < len(text) and text[cursor + 1] == "'":
                cursor += 2
                continue
            return cursor + 1
        cursor += 1
    return len(text)


def _skip_dq(text: str, index: int) -> int:
    cursor = index + 1
    while cursor < len(text):
        if text[cursor] == "`":
            cursor += 2
            continue
        if text[cursor] == '"':
            return cursor + 1
        cursor += 1
    return len(text)


def _split_pwsh_op(text: str, op: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    cursor = 0
    depth = 0
    while cursor < len(text):
        char = text[cursor]
        if char in "'\"":
            end = _skip_sq(text, cursor) if char == "'" else _skip_dq(text, cursor)
            buf.append(text[cursor:end])
            cursor = end
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        if (
            depth == 0
            and text[cursor:cursor + len(op)].lower() == op.lower()
            and _pwsh_edge(text, cursor, cursor + len(op))
        ):
            parts.append("".join(buf))
            buf = []
            cursor += len(op)
            continue
        buf.append(char)
        cursor += 1
    parts.append("".join(buf))
    return parts


def _pwsh_disjunct_false(part: str) -> bool:
    if re.sub(r"\s+", "", part).lower() == "$false":
        return True
    arms = _split_pwsh_op(part, "-and")
    if len(arms) > 1:
        return any(re.sub(r"\s+", "", arm).lower() == "$false" for arm in arms)
    return False


def _pwsh_condition_false(condition: str) -> bool:
    arms = [arm for arm in _split_pwsh_op(condition, "-or") if arm.strip()]
    return bool(arms) and all(_pwsh_disjunct_false(arm) for arm in arms)


def _read_pwsh_word(text: str, index: int) -> tuple[str, int] | None:
    cursor = index
    if text[cursor] == "$":
        cursor += 1
    if cursor >= len(text) or not (text[cursor].isalpha() or text[cursor] == "_"):
        return None
    cursor += 1
    while cursor < len(text) and (text[cursor].isalnum() or text[cursor] == "_"):
        cursor += 1
    return text[index:cursor], cursor


def _skip_pwsh_ws(text: str, index: int) -> int:
    while index < len(text) and text[index] in " \t\r\n":
        index += 1
    return index


def _read_pwsh_paren(text: str, index: int) -> tuple[str, int]:
    depth = 0
    cursor = index
    while cursor < len(text):
        char = text[cursor]
        if char in "'\"":
            cursor = _skip_sq(text, cursor) if char == "'" else _skip_dq(text, cursor)
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[index + 1:cursor], cursor + 1
        cursor += 1
    return text[index + 1:], len(text)


# Residual if(0), while, trap, try, and uncalled function or scriptblock shapes belong to scripts/check-ffmpeg-hash-gate.ps1.
def powershell_reachable(text: str) -> str:
    """PowerShell that can run. Comments, strings, here-strings, if($false), and code after exit/return are gone.

    A reachable throw keeps the words sha256 mismatch so the hash-gate matcher can see them.
    #861 exact-matches the workflow step body; this tokenizer does not change that body.
    """
    out: list[str] = []
    scopes = [_PwshScope(False)]
    index = 0
    pending_dead_block = False
    pending_dead_stmt = False
    at_stmt = True

    def dead() -> bool:
        top = scopes[-1]
        return top.dead or top.killed or pending_dead_stmt

    def emit(piece: str) -> None:
        if not dead():
            out.append(piece)

    while index < len(text):
        if text.startswith("<#", index):
            end = text.find("#>", index + 2)
            chunk = text[index:] if end < 0 else text[index:end + 2]
            out.append("\n" * chunk.count("\n"))
            index = len(text) if end < 0 else end + 2
            continue
        if text[index] == "#":
            end = text.find("\n", index)
            out.append("\n")
            at_stmt = True
            pending_dead_stmt = False
            index = len(text) if end < 0 else end + 1
            continue
        if text[index] == "@" and index + 2 < len(text) and text[index + 1] in "'\"":
            closer = "\n'@" if text[index + 1] == "'" else '\n"@'
            line_end = index + 2
            if line_end < len(text) and text[line_end] == "\r":
                line_end += 1
            if line_end < len(text) and text[line_end] == "\n":
                end = text.find(closer, line_end)
                chunk = text[index:] if end < 0 else text[index:end + len(closer)]
                out.append("\n" * chunk.count("\n"))
                index = len(text) if end < 0 else end + len(closer)
                continue
        if text[index] in "'\"":
            end = _skip_sq(text, index) if text[index] == "'" else _skip_dq(text, index)
            content = text[index + 1:end - 1] if end > index and text[end - 1:end] == text[index] else text[index + 1:end]
            if "sha256 mismatch" in content.lower():
                emit('"sha256 mismatch"')
            else:
                emit('""')
            at_stmt = False
            index = end
            continue
        char = text[index]
        if char == "\n":
            out.append("\n")
            at_stmt = True
            pending_dead_stmt = False
            index += 1
            continue
        if char in " \t\r":
            emit(char)
            index += 1
            continue
        if char == "{":
            if pending_dead_block:
                scopes.append(_PwshScope(True))
                pending_dead_block = False
            else:
                scopes.append(_PwshScope(dead()))
            emit("{")
            at_stmt = True
            index += 1
            continue
        if char == "}":
            if len(scopes) > 1:
                scopes.pop()
            emit("}")
            at_stmt = True
            index += 1
            continue
        if char == ";":
            emit(";")
            at_stmt = True
            pending_dead_stmt = False
            index += 1
            continue
        word = _read_pwsh_word(text, index)
        if word is not None:
            token, nxt = word
            lowered = token.lower()
            if lowered == "if" and at_stmt and not dead():
                paren_at = _skip_pwsh_ws(text, nxt)
                if paren_at < len(text) and text[paren_at] == "(":
                    condition, after = _read_pwsh_paren(text, paren_at)
                    body_at = _skip_pwsh_ws(text, after)
                    if _pwsh_condition_false(condition):
                        if body_at < len(text) and text[body_at] == "{":
                            pending_dead_block = True
                            index = body_at
                        else:
                            pending_dead_stmt = True
                            index = body_at
                        continue
                    emit("if ")
                    emit(condition)
                    at_stmt = False
                    index = after
                    continue
            if lowered in ("exit", "return") and at_stmt and not dead():
                scopes[-1].killed = True
                at_stmt = False
                index = nxt
                continue
            emit(token)
            at_stmt = False
            index = nxt
            continue
        emit(char)
        at_stmt = False
        index += 1
    return "".join(out)


def workflow_hash_operator(job: str) -> str | None:
    """Return -ne or -eq from a reachable hash-gate throw."""
    for line in powershell_reachable(job).splitlines():
        match = re.search(r"\$LASTEXITCODE\s+(-ne|-eq)\s+0\b", line)
        if match and "throw" in line and "sha256 mismatch" in line:
            return match.group(1)
    return None


def ffmpeg_sha_enforced(job: str) -> bool:
    """The hash literal is not enough. A failed verifier must throw, and -eq must not."""
    reached = powershell_reachable(job)
    return (
        "scripts/verify_ffmpeg_zip_sha256.py" in reached
        and workflow_hash_operator(job) == "-ne"
    )


def _line_parts(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    if line.endswith("\r"):
        return line[:-1], "\r"
    return line, ""

def ffmpeg_reachable_exit_reset(job: str) -> bool:
    """True when LASTEXITCODE is set to 0 after the verifier and before the throw.

    The assignment may sit on the verifier line. The -ne throw can still be present.
    Only reachable PowerShell counts. The canonical-body gate is separate.
    """
    codes = powershell_reachable(job).splitlines()
    start = next(
        (index for index, code in enumerate(codes) if "scripts/verify_ffmpeg_zip_sha256.py" in code),
        None,
    )
    if start is None:
        return False
    end = None
    for index in range(start, len(codes)):
        code = codes[index]
        if (
            re.search(r"\$LASTEXITCODE\s+-ne\s+0\b", code)
            and "throw" in code
            and "sha256 mismatch" in code
        ):
            end = index
            break
    if end is None:
        return False
    return any(EXIT_RESET.search(code) for code in codes[start:end + 1])


def _line_body(line: str) -> str:
    """Line text after leading whitespace. Trailing characters stay."""
    return _line_parts(line)[0].lstrip(" \t")


def _newline_lines(text: str) -> list[str]:
    """Split on ``\\n`` only. U+2028, U+2029, and U+0085 stay inside the line.

    A trailing ``\\r`` is the YAML ``\\r\\n`` break, not body text.
    """
    lines = []
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        lines.append(line)
    return lines


def _forbidden_body_char(text: str) -> bool:
    """True when the ffmpeg body has a non-ASCII character or a Unicode line separator."""
    return any(ord(ch) > 127 or ch in UNICODE_LINE_SEPARATORS for ch in text)


def _norm_trailing_newline(text: str) -> str:
    """Drop one trailing newline. Internal whitespace stays."""
    if text.endswith("\r\n"):
        return text[:-2]
    if text.endswith("\n"):
        return text[:-1]
    return text


def ffmpeg_literal_block(job: str) -> tuple[str, list[str]] | None:
    """Return the chomp indicator and the raw ``run: |`` lines of the ffmpeg step.

    Lines are split on ``\\n`` only and still carry their YAML indent.
    """
    lines = _newline_lines(job)
    name_body = f"- name: {FFMPEG_STEP_NAME}"
    step_at = None
    step_indent = None
    for index, line in enumerate(lines):
        stripped = line.lstrip(" ")
        if stripped == name_body:
            step_at = index
            step_indent = len(line) - len(stripped)
            break
    if step_at is None or step_indent is None:
        return None
    run_at = None
    run_indent = None
    chomp = ""
    for index in range(step_at + 1, len(lines)):
        line = lines[index]
        if line.strip(" ") == "":
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= step_indent:
            break
        match = RUN_HEADER.match(line.lstrip(" "))
        if match:
            run_at = index
            run_indent = indent
            chomp = match.group(1)
            break
    if run_at is None or run_indent is None:
        return None
    content: list[str] = []
    for index in range(run_at + 1, len(lines)):
        line = lines[index]
        if line.strip(" ") == "":
            content.append(line)
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= run_indent:
            break
        content.append(line)
    return chomp, content


def ffmpeg_run_body(job: str) -> str | None:
    """Parsed ffmpeg ``run:`` value from the YAML tree. None when it will not load."""
    try:
        document = load_yaml(job)
    except UniqueYamlError:
        return None
    steps = ffmpeg_named_steps(document)
    if not steps:
        return None
    body = steps[0].get("run")
    if not isinstance(body, str):
        return None
    return body


def ffmpeg_body_is_canonical(job: str) -> bool:
    """True when the parsed ffmpeg run body is the canonical text.

    One trailing newline is the only ignored difference. Any non-ASCII
    character or U+2028/U+2029/U+0085 in the raw block fails the body.
    """
    found = ffmpeg_literal_block(job)
    if found is None:
        return False
    _chomp, raw_lines = found
    if _forbidden_body_char("\n".join(raw_lines)):
        return False
    body = ffmpeg_run_body(job)
    if body is None or _forbidden_body_char(body):
        return False
    return _norm_trailing_newline(body) == CANONICAL_FFMPEG_RUN


def iter_mappings(node: object):
    """Yield every mapping in a loaded YAML document."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from iter_mappings(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_mappings(item)


def ffmpeg_named_steps(document: object) -> list[dict]:
    """Mappings whose ``name`` is the ffmpeg install step."""
    return [
        mapping
        for mapping in iter_mappings(document)
        if mapping.get("name") == FFMPEG_STEP_NAME
    ]


def _raw_key_name(body: str) -> str | None:
    """Return the key on one step line. None when the line is not a key."""
    match = _RAW_STEP_KEY.match(body)
    if match is None:
        return None
    if match.group("plain") is not None:
        return match.group("plain")
    if match.group("dquote") is not None:
        return match.group("dquote")
    if match.group("squote") is not None:
        return match.group("squote").replace("''", "'")
    complex_name = match.group("complex")
    return complex_name.strip().strip("'\"") if complex_name else None


def raw_ffmpeg_step_keys_ok(job: str) -> bool:
    """The first ffmpeg step's raw key lines are exactly name, shell, and run.

    Quoted keys and ``?`` keys count. A line at key indent that is not one of
    those keys is refused. This is defense in depth beside the parsed tree.
    """
    try:
        start, end = ffmpeg_step_span(job)
    except ValueError:
        return False
    lines = job.split("\n")
    step_indent = len(lines[start]) - len(lines[start].lstrip(" "))
    key_indent = step_indent + 2
    seen: list[str] = []
    for line in lines[start:end]:
        if line.strip(" ") == "" or line.lstrip(" ").startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent > key_indent:
            continue
        if indent not in {step_indent, key_indent}:
            return False
        name = _raw_key_name(line.lstrip(" "))
        if name is None or name not in CANONICAL_FFMPEG_KEYS or name in seen:
            return False
        seen.append(name)
    return set(seen) == CANONICAL_FFMPEG_KEYS


def ffmpeg_step_shape_ok(job: str) -> bool:
    """True when the workflow has one canonical ffmpeg step and one verifier.

    The parsed keys are exactly ``name``, ``shell: pwsh``, and ``run``.
    A quoted key is a real key. An explicit ``?`` key, a repeated key, an
    anchor, an alias, or a merge key refuses the document. The raw step
    lines must name the same allowed keys.
    """
    if not raw_ffmpeg_step_keys_ok(job):
        return False
    try:
        steps = ffmpeg_named_steps(load_yaml(job))
    except UniqueYamlError:
        return False
    if job.count(CANONICAL_VERIFIER) != 1:
        return False
    if len(steps) != 1:
        return False
    step = steps[0]
    if set(step) != CANONICAL_FFMPEG_KEYS:
        return False
    return step.get("shell") == CANONICAL_FFMPEG_SHELL


def ffmpeg_exit_was_reset(job: str, *, exact_body: bool = True) -> bool:
    """True when the ffmpeg step is not the one canonical step.

    ``exact_body=False`` disables the gate so the mutation log can show it
    is load-bearing.
    """
    if not exact_body:
        return False
    if not ffmpeg_step_shape_ok(job):
        return True
    return not ffmpeg_body_is_canonical(job)


def windows_permissions_are_contents_read(job: str) -> bool:
    lines = job.splitlines()
    for index, line in enumerate(lines):
        if not re.match(r"^    permissions:\s*$", line):
            continue
        body = []
        for nxt in lines[index + 1:]:
            if nxt.strip() == "":
                continue
            if not nxt.startswith("      "):
                break
            body.append(nxt.split("#", 1)[0].strip())
        return body == ["contents: read"]
    return False


def drop_ffmpeg_enforcement(job: str) -> str:
    """Mutation: delete the throw line and keep the hash literal."""
    kept: list[str] = []
    dropped = False
    for line in job.splitlines(keepends=True):
        code = line.split("#", 1)[0]
        if (
            not dropped
            and "$LASTEXITCODE" in code
            and "throw" in code
            and "sha256 mismatch" in code
        ):
            dropped = True
            continue
        kept.append(line)
    if not dropped:
        raise ValueError("ffmpeg enforcement line was not present to delete")
    return "".join(kept)


def invert_hash_operator(job: str) -> str:
    """Mutation Claude ran: -ne becomes -eq, so a matching zip throws and a bad zip continues."""
    flipped = job.replace("$LASTEXITCODE -ne 0", "$LASTEXITCODE -eq 0", 1)
    if flipped == job:
        raise ValueError("ffmpeg -ne operator was not present to invert")
    return flipped


def flip_persist_credentials(job: str) -> str:
    """Mutation: persist-credentials: false becomes true, so the checkout keeps a token."""
    mutated = job.replace("persist-credentials: false", "persist-credentials: true", 1)
    if mutated == job:
        raise ValueError("persist-credentials: false was not present to flip")
    return mutated


# Quoted keys and a space before the colon do not contain the bare text
# "continue-on-error:". The step key set is checked on the parsed tree.
_CONTINUE_ON_ERROR_KEY = re.compile(
    r"""(?m)(?:^|[{,\s])(?:["']continue-on-error["']|continue-on-error)[ \t]*:"""
)


def windows_continues_on_error(job: str) -> bool:
    return _CONTINUE_ON_ERROR_KEY.search(job) is not None


def insert_windows_continue_on_error(job: str, line: str) -> str:
    """Mutation: put a continue-on-error key back on the Windows job."""
    needle = "runs-on: windows-latest\n"
    mutated = job.replace(needle, needle + "    " + line + "\n", 1)
    if mutated == job:
        raise ValueError("runs-on: windows-latest was not present to restore continue-on-error")
    return mutated


def reset_ffmpeg_exit(job: str) -> str:
    """Mutation from the #827 verdict: zero LASTEXITCODE on the verifier line."""
    return splice_same_line(job, "$LASTEXITCODE = 0")


def _find_canonical(lines: list[str], canonical: str) -> int:
    for index, line in enumerate(lines):
        if _line_body(line) == canonical:
            return index
    raise ValueError("canonical ffmpeg line was not present")


def replace_canonical_line(job: str, canonical: str, replacement: str) -> str:
    """Replace one exact canonical line. This does not parse PowerShell."""
    lines = job.splitlines(keepends=True)
    index = _find_canonical(lines, canonical)
    body, ending = _line_parts(lines[index])
    indent = re.match(r"[ \t]*", body).group(0)
    lines[index] = f"{indent}{replacement}{ending}"
    return "".join(lines)


def splice_exit_reset(job: str, statement: str) -> str:
    """Insert a line after the canonical verifier line."""
    lines = job.splitlines(keepends=True)
    index = _find_canonical(lines, CANONICAL_VERIFIER)
    body, ending = _line_parts(lines[index])
    indent = re.match(r"[ \t]*", body).group(0)
    lines.insert(index + 1, f"{indent}{statement}{ending or chr(10)}")
    return "".join(lines)


def splice_same_line(job: str, statement: str) -> str:
    """Put a trailing statement on the verifier line."""
    return replace_canonical_line(job, CANONICAL_VERIFIER, CANONICAL_VERIFIER + "; " + statement)


def join_verifier_and_throw(job: str) -> str:
    """Put the throw on the verifier line after `;` and delete the throw line."""
    lines = job.splitlines(keepends=True)
    verifier_at = _find_canonical(lines, CANONICAL_VERIFIER)
    throw_at = _find_canonical(lines, CANONICAL_THROW)
    if throw_at != verifier_at + 1:
        raise ValueError("canonical ffmpeg lines were not consecutive")
    body, ending = _line_parts(lines[verifier_at])
    indent = re.match(r"[ \t]*", body).group(0)
    lines[verifier_at] = f"{indent}{CANONICAL_VERIFIER}; {CANONICAL_THROW}{ending}"
    del lines[throw_at]
    return "".join(lines)


def insert_relative(job: str, canonical: str, statement: str, *, after: bool) -> str:
    """Insert one line before or after an exact canonical line. Split on ``\\n`` only."""
    lines = job.split("\n")
    found = None
    indent = ""
    for index, line in enumerate(lines):
        if line.lstrip(" ") == canonical:
            found = index
            indent = line[: len(line) - len(canonical)]
            break
    if found is None:
        raise ValueError("canonical line missing: " + canonical)
    lines.insert(found + (1 if after else 0), indent + statement)
    return "\n".join(lines)


def wrap_verifier_throw(job: str, before: str, after: str) -> str:
    """Put ``before`` on the line above the verifier and ``after`` on the line below the throw."""
    wrapped = insert_relative(job, CANONICAL_VERIFIER, before, after=False)
    return insert_relative(wrapped, CANONICAL_THROW, after, after=True)


def ffmpeg_step_span(job: str) -> tuple[int, int]:
    """Line range of the first ffmpeg step, split on ``\\n`` only."""
    lines = job.split("\n")
    name = f"- name: {FFMPEG_STEP_NAME}"
    start = None
    indent = None
    for index, line in enumerate(lines):
        if line.lstrip(" ") == name:
            start = index
            indent = len(line) - len(line.lstrip(" "))
            break
    if start is None or indent is None:
        raise ValueError("ffmpeg step was not present")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.strip(" ") == "":
            continue
        if len(line) - len(line.lstrip(" ")) <= indent:
            end = index
            break
    return start, end


def decoy_ffmpeg_step(job: str) -> str:
    """Put a skipped canonical copy before the real step and delete its throw."""
    lines = job.split("\n")
    start, end = ffmpeg_step_span(job)
    block = lines[start:end]
    decoy: list[str] = []
    for index, line in enumerate(block):
        decoy.append(line)
        if index == 0:
            key_indent = len(line) - len(line.lstrip(" ")) + 2
            decoy.append(f"{' ' * key_indent}if: ${{{{ false }}}}")
    real = [line for line in block if line.lstrip(" ") != CANONICAL_THROW]
    if len(real) == len(block):
        raise ValueError("ffmpeg throw was not present to delete on the real step")
    lines[start:end] = decoy + real
    return "\n".join(lines)


def duplicate_ffmpeg_run(job: str) -> str:
    """Append a second ``run:`` key to the ffmpeg step."""
    lines = job.split("\n")
    start, end = ffmpeg_step_span(job)
    run_indent = None
    for line in lines[start:end]:
        stripped = line.lstrip(" ")
        if stripped.startswith("run:"):
            run_indent = len(line) - len(stripped)
            break
    if run_indent is None:
        raise ValueError("ffmpeg run key was not present")
    lines.insert(end, f"{' ' * run_indent}run: Write-Output replaced")
    return "\n".join(lines)


def quoted_duplicate_run(job: str) -> str:
    """Append a second ``\"run\":`` key. YAML treats it as another ``run``."""
    lines = job.split("\n")
    start, end = ffmpeg_step_span(job)
    run_indent = None
    for line in lines[start:end]:
        stripped = line.lstrip(" ")
        if stripped.startswith("run:"):
            run_indent = len(line) - len(stripped)
            break
    if run_indent is None:
        raise ValueError("ffmpeg run key was not present")
    lines.insert(end, f'{" " * run_indent}"run": Write-Output replaced')
    return "\n".join(lines)


def quoted_if_and_unverified_install(job: str) -> str:
    """Put ``\"if\":`` on the canonical step and add an unhashed install step."""
    mutated = insert_ffmpeg_step_key(job, '"if": ${{ false }}')
    lines = mutated.split("\n")
    start, end = ffmpeg_step_span(mutated)
    indent = len(lines[start]) - len(lines[start].lstrip(" "))
    inner = " " * (indent + 2)
    body = " " * (indent + 4)
    extra = [
        f"{' ' * indent}- name: Install ffmpeg",
        f"{inner}shell: pwsh",
        f"{inner}run: |",
        f"{body}curl.exe -fsSL -o $env:RUNNER_TEMP\\ffmpeg.zip https://example.invalid/ffmpeg.zip",
        f"{body}Add-Content -Path $env:GITHUB_PATH -Value $env:RUNNER_TEMP",
    ]
    lines[end:end] = extra
    return "\n".join(lines)


def insert_complex_if(job: str) -> str:
    """Add an explicit ``? if`` key on the canonical ffmpeg step."""
    lines = job.split("\n")
    start, _end = ffmpeg_step_span(job)
    key_indent = len(lines[start]) - len(lines[start].lstrip(" ")) + 2
    pad = " " * key_indent
    lines.insert(start + 1, f"{pad}: ${{{{ false }}}}")
    lines.insert(start + 1, f"{pad}? if")
    return "\n".join(lines)


def insert_ffmpeg_step_key(job: str, key_line: str) -> str:
    """Insert one step-level key under the ffmpeg step name."""
    lines = job.split("\n")
    start, _end = ffmpeg_step_span(job)
    key_indent = len(lines[start]) - len(lines[start].lstrip(" ")) + 2
    lines.insert(start + 1, f"{' ' * key_indent}{key_line}")
    return "\n".join(lines)


def override_ffmpeg_shell(job: str) -> str:
    """Change the ffmpeg step shell and leave every other step alone."""
    lines = job.split("\n")
    start, end = ffmpeg_step_span(job)
    for index in range(start, end):
        if lines[index].lstrip(" ") == f"shell: {CANONICAL_FFMPEG_SHELL}":
            indent = len(lines[index]) - len(lines[index].lstrip(" "))
            lines[index] = f"{' ' * indent}shell: bash"
            return "\n".join(lines)
    raise ValueError("ffmpeg shell was not present")


def join_with_unicode_separator(job: str, sep: str) -> str:
    """Replace the newline between the verifier and the throw. Keep the throw indent.

    ``str.splitlines`` still sees two canonical lines. The raw block keeps ``sep``.
    """
    if sep not in UNICODE_LINE_SEPARATORS:
        raise ValueError("separator is not a Unicode line separator")
    needle = CANONICAL_VERIFIER + "\n"
    index = job.find(needle)
    if index < 0:
        raise ValueError("verifier line missing")
    newline_at = index + len(CANONICAL_VERIFIER)
    cursor = newline_at + 1
    while cursor < len(job) and job[cursor] == " ":
        cursor += 1
    if not job.startswith(CANONICAL_THROW, cursor):
        raise ValueError("throw is not the next line")
    return job[:newline_at] + sep + job[newline_at + 1:]


def prove_exit_reset_variants(windows_job: str) -> str:
    """The ffmpeg step must be the one canonical step.

    The ``run:`` body must equal one canonical text. The workflow must
    contain that step name once and the verifier command once, and the
    parsed step keys must be exactly ``name``, ``shell: pwsh``, and ``run``.
    A quoted key is a real key. An explicit ``?`` key, a duplicate key, an
    anchor, an alias, or a merge key refuses the document. The raw step
    lines must name the same keys. Turning the gate off lets those
    mutations through.
    """
    variants = (
        ("bare", "$LASTEXITCODE = 0"),
        ("global", "$global:LASTEXITCODE = 0"),
        ("script", "$script:LASTEXITCODE = 0"),
        ("env", "$env:LASTEXITCODE = 0"),
        ("lower", "$lastexitcode = 0"),
        ("mixed", "$LastExitCode = 0"),
        ("zeros", "$LASTEXITCODE = 00"),
        ("hex", "$LASTEXITCODE = 0x0"),
        ("plus", "$LASTEXITCODE = +0"),
        ("set_positional", "Set-Variable LASTEXITCODE 0"),
        ("set_named", "Set-Variable -Name LASTEXITCODE -Value 0"),
        ("set_swapped", "Set-Variable -Value 00 -Name LASTEXITCODE"),
        ("set_colon", "Set-Variable -Name:LASTEXITCODE -Value:0"),
        ("set_lower", "set-variable -name lastexitcode -value 0"),
        ("cmd", "cmd /c exit 0"),
        ("cmd_exe", "cmd.exe /c exit 0"),
        ("cmd_quoted", 'cmd /c "exit 0"'),
        ("cmd_lower", "CMD.EXE /C EXIT 00"),
        ("python", 'python -c "pass"'),
        ("git", "git --version"),
        ("braced", "${LASTEXITCODE} = 0"),
        ("braced_global", "${global:LASTEXITCODE} = 0"),
        ("float", "$LASTEXITCODE = 0.0"),
        ("decimal", "$LASTEXITCODE = 0d"),
        ("false", "$LASTEXITCODE = $false"),
        ("cast", "$LASTEXITCODE = [int]0"),
        ("expr", "$LASTEXITCODE = 0 * 1"),
        ("set_item", "Set-Item variable:LASTEXITCODE 0"),
        ("new_var", "New-Variable LASTEXITCODE 0 -Force"),
        ("cmd_d", "cmd /d /c exit 0"),
        ("cmd_b", "cmd /c exit /b 0"),
        ("assign_one", "$LASTEXITCODE = 1"),
        ("padded_one", "$LASTEXITCODE = 001"),
        ("set_one", "Set-Variable LASTEXITCODE 1"),
        ("set_other", "Set-Variable PATH 0"),
        ("cmd_one", "cmd /c exit 1"),
        ("env_other", "$env:RUNNER_TEMP = 0"),
    )
    caught: list[str] = []
    for name, statement in variants:
        mutated = splice_exit_reset(windows_job, statement)
        if not ffmpeg_sha_enforced(mutated):
            fail(f"{name} gap mutation dropped the -ne throw")
        problems = windows_job_problems(mutated)
        if GAP_PROBLEM not in problems:
            fail(f"{name} statement was not caught: {statement}")
        caught.append(name)

    same_line = {
        "python_same_line": 'python -c "pass"',
        "assign_same_line": "$LASTEXITCODE = 0",
        "set_item_same_line": "Set-Item variable:LASTEXITCODE 0",
    }
    for name, statement in same_line.items():
        mutated = splice_same_line(windows_job, statement)
        if not ffmpeg_sha_enforced(mutated) or not ffmpeg_exit_was_reset(mutated):
            fail(f"{name} was not caught: {statement}")
        caught.append(name)

    backtick = (
        '$x = "`""; ' + CANONICAL_VERIFIER + '; git --version; $y = "`""'
    )
    line_mutations = {
        "or_git": replace_canonical_line(windows_job, CANONICAL_VERIFIER, CANONICAL_VERIFIER + " || git --version"),
        "or_python": replace_canonical_line(windows_job, CANONICAL_VERIFIER, CANONICAL_VERIFIER + " || python -c 'pass'"),
        "or_cmd": replace_canonical_line(windows_job, CANONICAL_VERIFIER, CANONICAL_VERIFIER + " || cmd /c exit 0"),
        "and_git": replace_canonical_line(windows_job, CANONICAL_VERIFIER, CANONICAL_VERIFIER + " && git --version"),
        "pipe": replace_canonical_line(windows_job, CANONICAL_VERIFIER, CANONICAL_VERIFIER + " | git --version"),
        "trailing": replace_canonical_line(windows_job, CANONICAL_VERIFIER, CANONICAL_VERIFIER + " --help"),
        "trailing_space": replace_canonical_line(windows_job, CANONICAL_VERIFIER, CANONICAL_VERIFIER + " "),
        "backtick": replace_canonical_line(windows_job, CANONICAL_VERIFIER, backtick),
        "help": replace_canonical_line(
            windows_job, CANONICAL_VERIFIER, "python scripts/verify_ffmpeg_zip_sha256.py --help"
        ),
        "blank": splice_exit_reset(windows_job, ""),
        "comment": splice_exit_reset(windows_job, "# $LASTEXITCODE = 0"),
        "same_line_throw": join_verifier_and_throw(windows_job),
        "throw_or": replace_canonical_line(windows_job, CANONICAL_THROW, CANONICAL_THROW + " || git --version"),
        "throw_and_git": replace_canonical_line(
            windows_job,
            CANONICAL_THROW,
            'if ((git --version) -and $LASTEXITCODE -ne 0) { throw "ffmpeg zip sha256 mismatch: $expected" }',
        ),
        "throw_and_false": replace_canonical_line(
            windows_job,
            CANONICAL_THROW,
            'if ($LASTEXITCODE -ne 0 -and $false) { throw "ffmpeg zip sha256 mismatch: $expected" }',
        ),
    }
    # throw_and_false hides the throw from reachable PowerShell, so the hash
    # gate catches it as well as the canonical-body gate.
    hash_hidden_lines = {"throw_and_false"}
    for name, mutated in line_mutations.items():
        if mutated == windows_job:
            fail(f"{name} did not change the windows job")
        enforced = ffmpeg_sha_enforced(mutated)
        if name in hash_hidden_lines:
            if enforced:
                fail(f"{name} left a reachable hash throw")
        elif not enforced:
            fail(f"{name} was caught by the hash gate instead of the run body")
        problems = windows_job_problems(mutated)
        if GAP_PROBLEM not in problems:
            fail(f"{name} line was not caught")
        caught.append(name)

    after_throw = windows_job.replace(
        'throw "ffmpeg zip sha256 mismatch: $expected" }',
        'throw "ffmpeg zip sha256 mismatch: $expected" }\n          $LASTEXITCODE = 0',
        1,
    )
    if after_throw == windows_job:
        fail("could not place a statement after the ffmpeg throw")
    context = {
        "if_false": wrap_verifier_throw(windows_job, "if ($false) {", "}"),
        "block_comment": wrap_verifier_throw(windows_job, "<#", "#>"),
        "here_string": wrap_verifier_throw(windows_job, '$null = @"', '"@'),
        "backtick_continue": insert_relative(
            windows_job, CANONICAL_VERIFIER, "Write-Output `", after=False
        ),
        "function_python": insert_relative(
            windows_job, CANONICAL_VERIFIER, "function python { }", after=False
        ),
        "alias_python": insert_relative(
            windows_job, CANONICAL_VERIFIER, "Set-Alias python Write-Output", after=False
        ),
        "recompute_expected": insert_relative(
            windows_job,
            CANONICAL_VERIFIER,
            "$expected = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()",
            after=False,
        ),
        "u2028": join_with_unicode_separator(windows_job, "\u2028"),
        "u2029": join_with_unicode_separator(windows_job, "\u2029"),
        "u0085": join_with_unicode_separator(windows_job, "\u0085"),
        "after_throw": after_throw,
        "extra_indent": windows_job.replace(
            CANONICAL_VERIFIER, "  " + CANONICAL_VERIFIER, 1
        ).replace(CANONICAL_THROW, "  " + CANONICAL_THROW, 1),
    }
    # if ($false) and a block comment make the throw unreachable. The body
    # gate still has to catch them when the hash gate is not the question.
    hash_hidden_context = {"if_false", "block_comment", "here_string"}
    for name, mutated in context.items():
        if mutated == windows_job:
            fail(f"{name} did not change the windows job")
        enforced = ffmpeg_sha_enforced(mutated)
        if name in hash_hidden_context:
            if enforced:
                fail(f"{name} left a reachable hash throw")
        elif not enforced:
            fail(f"{name} was caught by the hash gate instead of the run body")
        raw = ffmpeg_literal_block(mutated)
        if raw is None:
            fail(f"{name} dropped the ffmpeg run block")
        if name in {"u2028", "u2029", "u0085"}:
            sep = {"u2028": "\u2028", "u2029": "\u2029", "u0085": "\u0085"}[name]
            if sep not in "\n".join(raw[1]):
                fail(f"{name} was split out of the raw ffmpeg run block")
            split_bodies = [line.lstrip(" \t") for line in mutated.splitlines()]
            verifier_at = split_bodies.index(CANONICAL_VERIFIER)
            if split_bodies[verifier_at + 1] != CANONICAL_THROW:
                fail(f"{name} is not the splitlines pair the old gate accepted")
        problems = windows_job_problems(mutated)
        if GAP_PROBLEM not in problems:
            fail(f"{name} body was not caught")
        caught.append(name)

    shape = {
        "decoy_if_false": decoy_ffmpeg_step(windows_job),
        "duplicate_run": duplicate_ffmpeg_run(windows_job),
        "quoted_run": quoted_duplicate_run(windows_job),
        "step_if": insert_ffmpeg_step_key(windows_job, "if: ${{ false }}"),
        "quoted_if": quoted_if_and_unverified_install(windows_job),
        "step_continue": insert_ffmpeg_step_key(windows_job, "continue-on-error: true"),
        "quoted_continue": insert_ffmpeg_step_key(windows_job, "'continue-on-error': true"),
        "step_env": insert_ffmpeg_step_key(windows_job, "env: {FOO: bar}"),
        "flow_dup": insert_ffmpeg_step_key(windows_job, "env: {FOO: 1, FOO: 2}"),
        "complex_if": insert_complex_if(windows_job),
        "shell_bash": override_ffmpeg_shell(windows_job),
    }
    # These refuse the document, so there is no parsed body to compare.
    loader_refusals = {"duplicate_run", "quoted_run", "flow_dup", "complex_if"}
    for name, mutated in shape.items():
        if mutated == windows_job:
            fail(f"{name} did not change the windows job")
        if not ffmpeg_sha_enforced(mutated):
            fail(f"{name} was caught by the hash gate instead of the step shape")
        body_ok = ffmpeg_body_is_canonical(mutated)
        if name in loader_refusals:
            if body_ok:
                fail(f"{name} still had a canonical parsed body")
        elif not body_ok:
            fail(f"{name} was caught by the first-step body check")
        problems = windows_job_problems(mutated)
        if GAP_PROBLEM not in problems:
            fail(f"{name} step shape was not caught")
        caught.append(name)
    if shape["decoy_if_false"].count(CANONICAL_VERIFIER) != 2:
        fail("decoy fixture did not keep a second verifier call")
    if shape["decoy_if_false"].count(FFMPEG_STEP_NAME) != 2:
        fail("decoy fixture did not keep two ffmpeg steps")
    if shape["quoted_if"].count(CANONICAL_VERIFIER) != 1:
        fail("quoted if fixture changed the verifier count")
    if shape["quoted_if"].count("\n      - name: Install ffmpeg\n") != 1 and shape["quoted_if"].count("- name: Install ffmpeg") != 1:
        fail("quoted if fixture dropped the unverified install step")
    quoted_doc = load_yaml(shape["quoted_if"])
    quoted_steps = ffmpeg_named_steps(quoted_doc)
    if len(quoted_steps) != 1 or quoted_steps[0].get("if") != "${{ false }}":
        fail("quoted if was not a real if key on the one ffmpeg step")
    continued = load_yaml(shape["quoted_continue"])
    continued_step = ffmpeg_named_steps(continued)[0]
    if continued_step.get("continue-on-error") is not True:
        fail("quoted continue-on-error was not a real key")
    for kind, sample in (
        ("duplicate", "a: 1\na: 2\n"),
        ("duplicate", "env: {FOO: 1, FOO: 2}\n"),
        ("duplicate", 'run: hello\n"run": replaced\n'),
        ("complex", "? if\n: ${{ false }}\n"),
        ("complex", "{? if: false}\n"),
        ("complex", "? [a, b]\n: 1\n"),
        ("anchor", "a: &id 1\n"),
        ("alias", "b: *id\n"),
        ("merge", "b:\n  <<: {x: 1}\n"),
    ):
        try:
            load_yaml(sample)
        except UniqueYamlError as exc:
            if exc.kind != kind:
                fail(f"{sample!r} raised {exc.kind}, not {kind}")
        else:
            fail(f"{sample!r} was loaded")
    if load_yaml("if: ${{ false }}\n") != {"if": "${{ false }}"}:
        fail("a GitHub expression was not an ordinary scalar")
    if load_yaml('"if": ${{ false }}\n') != {"if": "${{ false }}"}:
        fail("a quoted if key was not an ordinary key")
    if _raw_key_name('"if": ${{ false }}') != "if":
        fail("raw scan missed a double-quoted if key")
    if _raw_key_name("'continue-on-error': true") != "continue-on-error":
        fail("raw scan missed a single-quoted continue-on-error key")
    if _raw_key_name('"run": Write-Output replaced') != "run":
        fail("raw scan missed a double-quoted run key")
    if _raw_key_name("? if") != "if":
        fail("raw scan missed an explicit if key")
    if _raw_key_name(": ${{ false }}") is not None:
        fail("raw scan treated a complex-key value line as a key")

    parsed = ffmpeg_run_body(windows_job)
    if parsed != CANONICAL_FFMPEG_RUN + "\n":
        fail("live ffmpeg run body is not the canonical text plus one trailing newline")
    if not ffmpeg_body_is_canonical(windows_job):
        fail("live ffmpeg run body was refused")
    if _forbidden_body_char(CANONICAL_FFMPEG_RUN) or CANONICAL_FFMPEG_RUN.endswith(("\n", "\r")):
        fail("canonical ffmpeg run text must be ASCII with no trailing newline")
    if _norm_trailing_newline(parsed) != CANONICAL_FFMPEG_RUN:
        fail("one trailing newline was not the only normalized difference")
    if _norm_trailing_newline(parsed + "\n") == CANONICAL_FFMPEG_RUN:
        fail("a second trailing newline was treated as the one allowed newline")
    allowed = {"live": windows_job}
    for name, sample in allowed.items():
        if not ffmpeg_sha_enforced(sample):
            fail(f"allowed {name} lost the -ne throw")
        if not ffmpeg_body_is_canonical(sample):
            fail(f"allowed {name} lost the canonical run body")
        if ffmpeg_exit_was_reset(sample):
            fail(f"allowed {name} was refused")

    hidden = (
        ("if_false", context["if_false"]),
        ("block_comment", context["block_comment"]),
        ("here_string", context["here_string"]),
        ("backtick_continue", context["backtick_continue"]),
        ("function_python", context["function_python"]),
        ("alias_python", context["alias_python"]),
        ("recompute_expected", context["recompute_expected"]),
        ("u2028", context["u2028"]),
        ("u2029", context["u2029"]),
        ("u0085", context["u0085"]),
        ("python", splice_exit_reset(windows_job, 'python -c "pass"')),
        ("assignment", splice_exit_reset(windows_job, "$LASTEXITCODE = 0")),
        ("set_item", splice_exit_reset(windows_job, "Set-Item variable:LASTEXITCODE 0")),
        ("or_chain", line_mutations["or_git"]),
        ("decoy_if_false", shape["decoy_if_false"]),
        ("duplicate_run", shape["duplicate_run"]),
        ("step_if", shape["step_if"]),
        ("step_continue", shape["step_continue"]),
        ("step_env", shape["step_env"]),
        ("flow_dup", shape["flow_dup"]),
        ("shell_bash", shape["shell_bash"]),
        ("quoted_run", shape["quoted_run"]),
        ("quoted_if", shape["quoted_if"]),
        ("quoted_continue", shape["quoted_continue"]),
        ("complex_if", shape["complex_if"]),
    )
    hidden_names = []
    for name, sample in hidden:
        if GAP_PROBLEM in windows_job_problems(sample, exact_body=False):
            fail(f"turning off the run-body gate still caught {name}")
        if GAP_PROBLEM not in windows_job_problems(sample):
            fail(f"run-body gate on did not catch {name}")
        hidden_names.append(name)
    if not hidden_names:
        fail("run-body mutation log has an empty group")
    return (
        "body=" + ",".join(f"{name}=caught" for name in caught)
        + " allowed=" + ",".join(f"{name}=pass" for name in allowed)
        + " load_bearing=off_body=" + ",".join(hidden_names) + "=escaped"
    )


FFMPEG_THROW = 'if ($LASTEXITCODE -ne 0) { throw "ffmpeg zip sha256 mismatch: $expected" }'


def line_comment_hash_operator(job: str) -> str | None:
    """The pre-tokenization matcher. A multiline <# #> comment still looks live to it."""
    for line in job.splitlines():
        code = line.split("#", 1)[0]
        match = re.search(r"\$LASTEXITCODE\s+(-ne|-eq)\s+0\b", code)
        if match and "throw" in code and "sha256 mismatch" in code:
            return match.group(1)
    return None


def hide_ffmpeg_throw(job: str, wrapped: str) -> str:
    if job.count(FFMPEG_THROW) != 1:
        raise ValueError("ffmpeg throw was not present once")
    return job.replace(FFMPEG_THROW, wrapped, 1)


def prove_ffmpeg_throw_reachable(job: str) -> str:
    """Mutations that keep the throw text but make it unreachable."""
    if workflow_hash_operator(job) != "-ne" or not ffmpeg_sha_enforced(job):
        fail("live ffmpeg throw is not a reachable -ne gate")
    if ffmpeg_exit_was_reset(job):
        fail("live ffmpeg throw was treated as an exit reset")
    hides = {
        "block": "<#\n" + FFMPEG_THROW + "\n#>",
        "inline_block": "<# " + FFMPEG_THROW + " #>",
        "here_literal": "@'\n" + FFMPEG_THROW + "\n'@",
        "here_expand": '@"\n' + FFMPEG_THROW + '\n"@',
        "if_false": "if ($false) { " + FFMPEG_THROW + " }",
        "if_false_case": "If ($False) { " + FFMPEG_THROW + " }",
        "and_false": 'if ($LASTEXITCODE -ne 0 -and $false) { throw "ffmpeg zip sha256 mismatch: $expected" }',
        "or_true": None,
        "exit": "exit 0\n" + FFMPEG_THROW,
        "return": "return\n" + FFMPEG_THROW,
        "string": "$note = '" + FFMPEG_THROW + "'",
    }
    # A false disjunct beside a true one must stay reachable.
    or_true = 'if ($false -or $true) { ' + FFMPEG_THROW + " }"
    if not ffmpeg_sha_enforced(hide_ffmpeg_throw(job, or_true)):
        fail("if ($false -or $true) hid a reachable throw")
    conditional_exit = "if ($true) { exit }\n" + FFMPEG_THROW
    if not ffmpeg_sha_enforced(hide_ffmpeg_throw(job, conditional_exit)):
        fail("exit inside if hid a later throw")
    fooled = ("block", "here_literal", "here_expand", "if_false", "and_false", "exit", "return", "string")
    for name, wrapped in hides.items():
        if wrapped is None:
            continue
        mutated = hide_ffmpeg_throw(job, wrapped)
        old = line_comment_hash_operator(mutated)
        if name in fooled and old != "-ne":
            fail("line-comment matcher was not fooled by " + name)
        if name == "inline_block" and old is not None:
            fail("single-line block comment still matched after a hash split")
        if ffmpeg_sha_enforced(mutated) or workflow_hash_operator(mutated) is not None:
            fail("hidden ffmpeg throw still counted as enforced: " + name)
        problems = windows_job_problems(mutated)
        if not any(
            problem == "check-all-windows does not enforce the ffmpeg zip sha256"
            for problem in problems
        ):
            fail("hidden ffmpeg throw was not caught: " + name)
    return "throw_hidden=caught"


def windows_job_problems(job: str, *, exact_body: bool = True) -> list[str]:
    problems: list[str] = []
    for needle in (
        "runs-on: windows-latest",
        "github.event_name == 'pull_request' || github.event_name == 'push'",
        "python scripts/check-all.py",
        "requirements-sensors.py311.lock",
        "--require-hashes",
        FFMPEG_ZIP_SHA256,
        "ffmpeg-7.1.1-full_build.zip",
        "core.autocrlf false",
        CHECKOUT,
        "# actions/checkout v7.0.1",
        SETUP_PYTHON,
        "# actions/setup-python v7.0.0",
        UPLOAD_ARTIFACT,
        "# actions/upload-artifact v7.0.2",
        "name: check-all-windows",
        "if-no-files-found: error",
        "if: always()",
        "persist-credentials: false",
        "fetch-depth: 0",
        "git show <sha>:path",
        "scripts/check-ffmpeg-hash-gate.ps1",
    ):
        if needle not in job:
            problems.append(f"check-all-windows missing {needle}")
    if windows_continues_on_error(job):
        problems.append("check-all-windows must not continue on error")
    if not ffmpeg_sha_enforced(job):
        problems.append("check-all-windows does not enforce the ffmpeg zip sha256")
    if ffmpeg_exit_was_reset(job, exact_body=exact_body):
        problems.append(GAP_PROBLEM)
    if ffmpeg_reachable_exit_reset(job):
        problems.append("check-all-windows resets LASTEXITCODE after the ffmpeg hash gate")
    if not windows_permissions_are_contents_read(job):
        problems.append("check-all-windows permissions must be contents: read only")
    if "statuses:" in job:
        problems.append("check-all-windows must not grant statuses")
    extra_actions = [
        use for use in re.findall(r"uses:\s*(\S+)", job)
        if use not in WINDOWS_ACTIONS
    ]
    if extra_actions:
        problems.append(
            "check-all-windows uses an action outside the allowlist: " + ", ".join(extra_actions)
        )
    if "secrets." in job or "upload_gha_artifact" in job or "ACTIONS_RUNTIME_TOKEN" in job:
        problems.append("check-all-windows must not read a secret or call the internal artifact API")
    return problems


HASH_GATE = ROOT / "scripts" / "verify_ffmpeg_zip_sha256.py"
HASH_GATE_PARSER = ROOT / "scripts" / "check-ffmpeg-hash-gate.ps1"
HASH_GATE_PARSER_NEEDLES = (
    "Parser]::ParseInput",
    "EndBlock",
    "TrapStatementAst",
    "BreakStatementAst",
    "ContinueStatementAst",
    "ExitStatementAst",
    "ReturnStatementAst",
    "TokenKind]::Ine",
    "FunctionDefinitionAst",
    "MemberExpressionAst",
    "AssignmentStatementAst",
    "Set-Alias",
    "New-Alias",
    "scripts/verify_ffmpeg_zip_sha256.py",
    "'if-zero'",
    "'if-null'",
    "'if-not'",
    "'if-bang'",
    "'if-parens'",
    "'if-var'",
    "'if-backtick'",
    "'while-false'",
    "'function-never'",
    "'scriptblock'",
    "'else-branch'",
    "'try-catch'",
    "'trap'",
    "'break-before'",
    "'midword-hash'",
    "'function-python'",
    "'filter-python'",
    "'function-global-python'",
    "'set-alias'",
    "'new-alias'",
    "'sal-python'",
    "'expected-reassign'",
    "'expected-deadbeef'",
    "'static-exit'",
    "'static-system-exit'",
    "'static-failfast'",
    "'verify-c'",
    "'verify-help'",
    "'verify-path'",
)


def hash_gate_parser_problems(text: str) -> list[str]:
    """Linux presence pin. The parser itself runs on the Windows job."""
    problems: list[str] = []
    for needle in HASH_GATE_PARSER_NEEDLES:
        if needle not in text:
            problems.append(f"ffmpeg hash-gate parser missing {needle}")
    return problems


def drop_hash_gate_parser_step(job: str) -> str:
    """Mutation: the Windows job no longer invokes the parser allowlist."""
    mutated = job.replace(
        "scripts/check-ffmpeg-hash-gate.ps1",
        "scripts/check-ffmpeg-hash-gate-removed.ps1",
        1,
    )
    if mutated == job:
        raise ValueError("ffmpeg hash-gate parser step was not present to remove")
    return mutated


def hash_gate_exits(script: Path, data: bytes, expected: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp) / "fixture.bin"
        fixture.write_bytes(data)
        proc = subprocess.run(
            [sys.executable, str(script), "--path", str(fixture), "--expected", expected],
            text=True,
            capture_output=True,
            timeout=15,
        )
        return proc.returncode


def prove_ffmpeg_hash_gate() -> str:
    """Run the real verifier, then a copy whose comparison is inverted."""
    if not HASH_GATE.is_file():
        fail("missing ffmpeg hash gate: scripts/verify_ffmpeg_zip_sha256.py")
    source = HASH_GATE.read_text(encoding="utf-8")
    if source.count("got != expected") != 1:
        fail("ffmpeg hash gate must compare with got != expected exactly once")
    data = b"not-the-ffmpeg-zip"
    wrong = "0" * 64
    right = hashlib.sha256(data).hexdigest()
    mismatch = hash_gate_exits(HASH_GATE, data, wrong)
    match = hash_gate_exits(HASH_GATE, data, right)
    if mismatch == 0 or match != 0:
        fail(
            "ffmpeg hash gate fixture failed: "
            f"wrong_digest_exit={mismatch} match_exit={match}"
        )
    inverted = source.replace("got != expected", "got == expected", 1)
    with tempfile.TemporaryDirectory() as tmp:
        mutated = Path(tmp) / "verify_ffmpeg_zip_sha256.py"
        mutated.write_text(inverted, encoding="utf-8")
        inverted_exit = hash_gate_exits(mutated, data, wrong)
    if inverted_exit != 0:
        fail("inverting got != expected still rejected a wrong digest")
    return f"wrong_digest_exit={mismatch} match_exit={match} inverted_operator_exit={inverted_exit}"


def precheck_permission_problems(text: str) -> list[str]:
    """Writers that call the precheck helper must read the commit status, not forge it."""
    if PRECHECK_HELPER not in text:
        return []
    problems: list[str] = []
    if not re.search(r"(?m)^\s*actions:\s*write\s*(?:#.*)?$", text):
        problems.append("lacks explicit actions: write permission")
    if not re.search(r"(?m)^\s*statuses:\s*read\s*(?:#.*)?$", text):
        problems.append("lacks explicit statuses: read permission")
    if re.search(r"(?m)^\s*statuses:\s*write\s*(?:#.*)?$", text):
        problems.append("must not grant statuses: write")
    return problems


def posix_bash(
    platform: str,
    found: str | None,
    *,
    system32: bool,
    git_bash: str | None,
) -> str | None:
    """Return a POSIX bash. System32 bash.exe is the WSL launcher, not a shell."""
    if platform == "win32" and system32:
        return git_bash
    return found


def resolve_posix_bash() -> str:
    found = shutil.which("bash")
    system32 = False
    git_bash = None
    if sys.platform == "win32" and found:
        bash_path = Path(found).resolve()
        system32 = (
            bash_path.name.lower() == "bash.exe"
            and bash_path.parent.name.lower() == "system32"
        )
        if system32:
            git = shutil.which("git")
            candidate = (Path(git).resolve().parents[1] / "bin" / "bash.exe") if git else None
            if candidate and candidate.is_file():
                git_bash = str(candidate)
    bash = posix_bash(sys.platform, found, system32=system32, git_bash=git_bash)
    if not bash:
        fail("POSIX bash is required for the gh api label selftest")
    return bash


def prove_gh_api_labels(helper: Path) -> str:
    """A 403 from either gh api call is named, and deleting the name fails."""
    git_bash = r"C:\Program Files\Git\bin\bash.exe"
    system32_bash = r"C:\Windows\System32\bash.exe"
    if posix_bash("win32", system32_bash, system32=True, git_bash=git_bash) != git_bash:
        fail("Windows System32 bash must not run the gh api label selftest")
    if posix_bash("win32", system32_bash, system32=True, git_bash=None) is not None:
        fail("Windows without Git Bash must not fall through to the WSL launcher")
    if posix_bash("linux", "/bin/bash", system32=False, git_bash=None) != "/bin/bash":
        fail("Linux bash must still run the gh api label selftest")
    bash = resolve_posix_bash()
    live = subprocess.run(
        [bash, str(helper), "--selftest"],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if live.returncode != 0 or "status_403=named" not in live.stdout or "checks_403=named" not in live.stdout:
        fail(
            "gh api label selftest failed: "
            f"rc={live.returncode} stdout={live.stdout!r} stderr={live.stderr!r}"
        )
    source = helper.read_text(encoding="utf-8")
    muted = source.replace('echo "::error::gh api ${label} failed" >&2\n', "", 1)
    if muted == source:
        fail("gh api label echo was not present to delete")
    with tempfile.TemporaryDirectory() as tmp:
        mutant = Path(tmp) / "push-main-with-check-all.sh"
        mutant.write_text(muted, encoding="utf-8")
        hidden = subprocess.run(
            [bash, str(mutant), "--selftest"],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    if hidden.returncode == 0:
        fail("dropping the gh api label still passed selftest")
    intake = (WORKFLOWS / "vfmedia-intake.yml").read_text(encoding="utf-8")
    stripped = re.sub(r"(?m)^\s*statuses:\s*read\s*(?:#.*)?\n", "", intake, count=1)
    if stripped == intake:
        fail("vfmedia-intake statuses: read line was not present to delete")
    if not any("statuses: read" in problem for problem in precheck_permission_problems(stripped)):
        fail("removing statuses: read was not caught")
    widened = intake.replace("statuses: read", "statuses: write", 1)
    if widened == intake or not any(
        "statuses: write" in problem for problem in precheck_permission_problems(widened)
    ):
        fail("statuses: write on a machine writer was not caught")
    jobs = (WORKFLOWS / "jobs-write-through.yml").read_text(encoding="utf-8")
    if precheck_permission_problems(jobs):
        fail("jobs-write-through " + "; ".join(precheck_permission_problems(jobs)))
    return "gh_api_label=caught status_read_removed=caught status_write=caught"


def main() -> int:
    helper = ROOT / PRECHECK_HELPER
    if not helper.is_file():
        fail(f"missing machine-writer precheck helper: {PRECHECK_HELPER}")
    helper_text = helper.read_text(encoding="utf-8")
    for needle in (
        'target_branch="${1:-main}"',
        'git rebase "origin/$target_branch"',
        'scripts/sensor_selector.py',
        'machine_write_class',
        'AUTHORITY_SECURITY',
        'class=$machine_write_class',
        'precheck_log',
        'post_push=exact_sha_precheck_reused',
        'machine-check/',
        'gh workflow run "$workflow_file"',
        'gh run watch "$check_run_id"',
        '.name == "check-all"',
        '.app.slug == "github-actions"',
        'commits/$head_sha/status',
        '.context == "check-all"',
        '.state == "success"',
        'gh_api commit-check-runs',
        'gh_api commit-status',
        '::error::gh api ${label} failed',
        'git merge-base --is-ancestor "origin/$target_branch" "$head_sha"',
        'git push origin "HEAD:refs/heads/$target_branch"',
        'git ls-remote origin "refs/heads/$target_branch"',
        'post-push remote head mismatch',
        'if [[ "$machine_write_class" == "AUTHORITY_SECURITY" ]]',
        '-f execution=main_full',
        'SENSORS [0-9]+ mode=full',
        'OK suite passed=[0-9]+',
    ):
        if needle not in helper_text:
            fail(f"machine-writer precheck helper missing invariant: {needle}")
    if re.search(r"git\s+push\s+(?:--force|-f)\b", helper_text):
        fail("machine-writer precheck helper must never force-push")
    raw_api = [
        line.strip()
        for line in helper_text.splitlines()
        if re.search(r"""gh api\s+["']""", line.split("#", 1)[0])
        and 'gh api "$@"' not in line
    ]
    if raw_api:
        fail("unlabeled gh api call: " + raw_api[0])
    label_evidence = prove_gh_api_labels(helper)

    core_workflow = (WORKFLOWS / "check-all.yml").read_text(encoding="utf-8")
    for needle in (
        "workflow_dispatch:",
        "github.event_name == 'workflow_dispatch'",
        "--selection sensor-selection.json",
        "statuses: write",
        "statuses/$GITHUB_SHA",
        "context=check-all",
        "state=success",
        "execution:",
        "machine_precheck",
        "main_full",
        "inputs.execution == 'main_full'",
    ):
        if needle not in core_workflow:
            fail(f"Core Sensors missing machine precheck surface: {needle}")
    if re.search(r"(?m)^\s*schedule:\s*$", core_workflow) or "cron:" in core_workflow:
        fail("check-all.yml must not schedule")
    if "  check-all-windows:" not in core_workflow:
        fail("check-all.yml missing check-all-windows job")
    try:
        workflow_doc = load_yaml(core_workflow)
    except UniqueYamlError as exc:
        fail(f"check-all.yml YAML {exc.kind}: {exc.detail}")
    workflow_steps = ffmpeg_named_steps(workflow_doc)
    if len(workflow_steps) != 1:
        fail("check-all.yml must contain exactly one ffmpeg install step")
    if core_workflow.count(CANONICAL_VERIFIER) != 1:
        fail("check-all.yml must call the ffmpeg verifier exactly once")
    ffmpeg_step = workflow_steps[0]
    if set(ffmpeg_step) != CANONICAL_FFMPEG_KEYS or ffmpeg_step.get("shell") != CANONICAL_FFMPEG_SHELL:
        fail("ffmpeg install step keys must be name, shell: pwsh, and run")
    if not raw_ffmpeg_step_keys_ok(core_workflow):
        fail("ffmpeg install step raw keys must be exactly name, shell, and run")
    windows_job = core_workflow.split("  check-all-windows:", 1)[1]
    for problem in windows_job_problems(windows_job):
        fail(problem)
    try:
        mutated = drop_ffmpeg_enforcement(windows_job)
    except ValueError as exc:
        fail(str(exc))
    if FFMPEG_ZIP_SHA256 not in mutated:
        fail("ffmpeg enforcement mutation also deleted the hash literal")
    mutated_problems = windows_job_problems(mutated)
    if not any(problem == "check-all-windows does not enforce the ffmpeg zip sha256" for problem in mutated_problems):
        fail("deleting the ffmpeg sha256 enforcement line was not caught")
    try:
        flipped = invert_hash_operator(windows_job)
    except ValueError as exc:
        fail(str(exc))
    if ffmpeg_sha_enforced(flipped) or workflow_hash_operator(flipped) != "-eq":
        fail("flipping the ffmpeg hash operator from -ne to -eq was not caught")
    flipped_problems = windows_job_problems(flipped)
    if not any(problem == "check-all-windows does not enforce the ffmpeg zip sha256" for problem in flipped_problems):
        fail("the -ne to -eq mutation still passed the windows job sensor")
    try:
        reset = reset_ffmpeg_exit(windows_job)
    except ValueError as exc:
        fail(str(exc))
    if not ffmpeg_sha_enforced(reset):
        fail("the LASTEXITCODE reset mutation must keep the -ne throw")
    reset_problems = windows_job_problems(reset)
    if GAP_PROBLEM not in reset_problems:
        fail("a statement on the ffmpeg verifier line was not caught")
    if not any(
        problem == "check-all-windows resets LASTEXITCODE after the ffmpeg hash gate"
        for problem in reset_problems
    ):
        fail("resetting LASTEXITCODE after the ffmpeg hash gate was not caught")
    try:
        creds = flip_persist_credentials(windows_job)
    except ValueError as exc:
        fail(str(exc))
    cred_problems = windows_job_problems(creds)
    if not any("persist-credentials: false" in problem for problem in cred_problems):
        fail("flipping persist-credentials to true was not caught")
    continue_variants = (
        "continue-on-error: true",
        '"continue-on-error": true',
        "'continue-on-error': true",
        "continue-on-error : true",
        '"continue-on-error" : true',
    )
    for line in continue_variants:
        try:
            continued = insert_windows_continue_on_error(windows_job, line)
        except ValueError as exc:
            fail(str(exc))
        if line != "continue-on-error: true" and "continue-on-error:" in line:
            fail("continue-on-error variant fixture still contains the bare needle")
        continued_problems = windows_job_problems(continued)
        if not any(
            problem == "check-all-windows must not continue on error"
            for problem in continued_problems
        ):
            fail("continue-on-error variant was not caught: " + line)
    variant_evidence = prove_exit_reset_variants(windows_job)
    if not HASH_GATE_PARSER.is_file():
        fail("missing ffmpeg hash-gate parser: scripts/check-ffmpeg-hash-gate.ps1")
    parser_text = HASH_GATE_PARSER.read_text(encoding="utf-8")
    for problem in hash_gate_parser_problems(parser_text):
        fail(problem)
    stripped = parser_text.replace("'if-zero'", "'gone'", 1)
    if stripped == parser_text:
        fail("if-zero mutant label was not present to delete")
    stripped_problems = hash_gate_parser_problems(stripped)
    if not any(
        problem == "ffmpeg hash-gate parser missing 'if-zero'"
        for problem in stripped_problems
    ):
        fail("deleting the if-zero mutant label was not caught")
    try:
        dropped_parser = drop_hash_gate_parser_step(windows_job)
    except ValueError as exc:
        fail(str(exc))
    dropped_parser_problems = windows_job_problems(dropped_parser)
    if not any(
        problem == "check-all-windows missing scripts/check-ffmpeg-hash-gate.ps1"
        for problem in dropped_parser_problems
    ):
        fail("removing the ffmpeg hash-gate parser step was not caught")
    throw_evidence = prove_ffmpeg_throw_reachable(windows_job)
    gate_evidence = prove_ffmpeg_hash_gate()
    print(
        "OK check-all-windows ffmpeg-sha-enforce "
        "delete=caught operator_flip=caught exit_reset=caught credentials=caught "
        f"continue_on_error=caught variants=quoted,spaced {variant_evidence} "
        f"parser_step=caught label=caught {throw_evidence} "
        f"{gate_evidence} permissions=contents:read"
    )
    pin_evidence = prove_workflow_action_pins(core_workflow)
    for problem in scan_pin_paths(discover_pin_paths(ROOT)):
        fail(problem)
    print(f"OK workflow-action-pins {pin_evidence}")
    if core_workflow.count("context=check-all") != 1:
        fail("check-all status context must stay the single required Linux context")
    if "context=check-all-windows" in core_workflow:
        fail("check-all-windows must not publish a status")

    writers = []
    for path in sorted(list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml"))):
        text = path.read_text(encoding="utf-8")
        if not is_machine_writer(text):
            continue
        rel = path.relative_to(ROOT).as_posix()
        writers.append(rel)
        allowed = marker_paths(text)
        if not allowed:
            fail(f"machine writer {rel} has git push but no {MARKER} contract")
        if not has_write_permission(text):
            fail(f"machine writer {rel} lacks explicit contents: write permission")
        if has_unprotected_default_push(text):
            fail(f"machine writer {rel} can push the default branch without {PRECHECK_HELPER}")
        for problem in precheck_permission_problems(text):
            fail(f"prechecked machine writer {rel} {problem}")
        for line in text.splitlines():
            cmd = line.strip()
            if re.fullmatch(r"git add (?:-A|--all|\.)", cmd):
                fail(f"machine writer {rel} uses unrestricted staging: {cmd}")
            if re.match(r"git push\s+(?:--force|-f)\b", cmd):
                fail(f"machine writer {rel} may force-push: {cmd}")
        add_lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("git add ")]
        if not add_lines:
            fail(f"machine writer {rel} pushes but has no explicit git add line")
        if any("${existing[@]}" in ln for ln in add_lines) and "paths=(" not in text:
            fail(f"machine writer {rel} has dynamic staging without bounded paths array")
    if not writers:
        fail("no production machine writers discovered; sensor query likely broken")
    print(
        "OK machine-writers="
        f"{len(writers)} allowlisted force_push=0 unrestricted_stage=0 "
        f"default_main=prechecked_exact_sha {label_evidence} statuses_read=required"
    )
    for writer in writers:
        print("- " + writer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
