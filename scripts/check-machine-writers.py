#!/usr/bin/env python3
from __future__ import annotations

import collections.abc
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from yaml.composer import Composer, ComposerError
from yaml.constructor import ConstructorError
from yaml.events import AliasEvent
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
EXIT_RESET = re.compile(r"\$LASTEXITCODE\s*=\s*0\b")
# Tag and branch refs are refused. This set is the only exception, and it starts empty.
ACTION_REF_ALLOWLIST: frozenset[str] = frozenset()
VERSION_COMMENT = re.compile(
    r"^\s*#\s+(?P<action>\S+/\S+)\s+v(?P<version>\d+\.\d+\.\d+)\s*$"
)
SHA_REF = re.compile(r"^[0-9a-f]{40}$")
DOCKER_DIGEST = re.compile(r"^docker://.+@sha256:[0-9a-f]{64}$")
MERGE_TAG = "tag:yaml.org,2002:merge"
DOCKER_DIGEST_REF = "docker://alpine@sha256:" + ("ab" * 32)


def previous_nonempty(lines: list[str], index: int) -> str:
    """Return the previous non-empty line. index is the 0-based current line."""
    cursor = index - 1
    while cursor >= 0 and lines[cursor].strip() == "":
        cursor -= 1
    return lines[cursor] if cursor >= 0 else ""


class DuplicateKeyRejectingSafeLoader(yaml.SafeLoader):
    """Safe loader that rejects duplicate keys and step/job anchors, aliases, and merges."""

    def __init__(self, stream):
        super().__init__(stream)
        self._stack: list[str] = []

    def _top(self) -> str:
        return self._stack[-1] if self._stack else ""

    def compose_node(self, parent, index):
        if self.check_event(AliasEvent) and self._top() in {"step", "job"}:
            event = self.peek_event()
            raise ComposerError(None, None, "alias refused on a step", event.start_mark)
        # AliasEvent.anchor is the alias name, not a definition. Only node-start anchors are refused here.
        if self._top() in {"step", "job"} and not self.check_event(AliasEvent):
            event = self.peek_event()
            if getattr(event, "anchor", None):
                raise ComposerError(None, None, "anchor refused on a step", event.start_mark)
        return Composer.compose_node(self, parent, index)

    def compose_sequence_node(self, anchor):
        start_event = self.get_event()
        tag = start_event.tag
        if tag is None or tag == "!":
            tag = self.resolve(SequenceNode, None, start_event.implicit)
        node = SequenceNode(
            tag, [], start_event.start_mark, None, flow_style=start_event.flow_style
        )
        if anchor is not None:
            self.anchors[anchor] = node
        index = 0
        under_steps = self._top() == "steps"
        while not self.check_event(yaml.events.SequenceEndEvent):
            if under_steps:
                self._stack.append("step")
            try:
                node.value.append(self.compose_node(node, index))
            finally:
                if under_steps:
                    self._stack.pop()
            index += 1
        end_event = self.get_event()
        node.end_mark = end_event.end_mark
        return node

    def compose_mapping_node(self, anchor):
        start_event = self.get_event()
        tag = start_event.tag
        if tag is None or tag == "!":
            tag = self.resolve(MappingNode, None, start_event.implicit)
        node = MappingNode(
            tag, [], start_event.start_mark, None, flow_style=start_event.flow_style
        )
        if anchor is not None:
            self.anchors[anchor] = node
        while not self.check_event(yaml.events.MappingEndEvent):
            item_key = self.compose_node(node, None)
            key_name = item_key.value if isinstance(item_key, ScalarNode) else None
            if self._top() in {"step", "job"} and (
                key_name == "<<" or getattr(item_key, "tag", "") == MERGE_TAG
            ):
                raise ComposerError(None, None, "merge key refused on a step", item_key.start_mark)
            pushed = None
            if self._top() == "jobs":
                pushed = "job"
            elif key_name == "steps":
                pushed = "steps"
            elif key_name == "jobs":
                pushed = "jobs"
            if pushed:
                self._stack.append(pushed)
            try:
                item_value = self.compose_node(node, item_key)
            finally:
                if pushed:
                    self._stack.pop()
            node.value.append((item_key, item_value))
        end_event = self.get_event()
        node.end_mark = end_event.end_mark
        return node

    def construct_mapping(self, node, deep=False):
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        if not isinstance(node, MappingNode):
            raise ConstructorError(
                None, None, "expected a mapping node, but found %s" % node.id, node.start_mark
            )
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, collections.abc.Hashable):
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found unhashable key",
                    key_node.start_mark,
                )
            if key in mapping:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found duplicate key %r" % (key,),
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


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


def _load_pin_document(text: str):
    loader = DuplicateKeyRejectingSafeLoader(text)
    try:
        node = loader.get_single_node()
        if node is not None:
            loader.construct_document(node)
        return node, None
    except yaml.YAMLError as exc:
        return None, exc
    finally:
        loader.dispose()


def action_pin_problems(
    text: str,
    *,
    path: str = "<fixture>",
    allowlist: frozenset[str] | None = None,
) -> list[str]:
    """Every remote uses is a 40-hex SHA plus a version comment, unless allowlisted.

    docker:// refs must be docker://...@sha256: and 64 lowercase hex. Local ./ refs
    stay local. The document is a PyYAML safe load: duplicate keys are refused, and
    anchors, aliases, and merge keys on steps and jobs are refused.
    """
    allowed = ACTION_REF_ALLOWLIST if allowlist is None else allowlist
    node, error = _load_pin_document(text)
    if error is not None:
        return [f"{path}: YAML refused: {error}"]
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
    _require(action_pin_problems(aliased), "alias refused", "step alias")
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
    job_alias = (
        "x-base: &job\n"
        "  # org/repo v1.2.3\n"
        "  uses: org/repo/.github/workflows/ci.yml@" + ("b" * 40) + "\n"
        "jobs:\n"
        "  call: *job\n"
    )
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


def workflow_hash_operator(job: str) -> str | None:
    """Return -ne or -eq from the throw that follows the hash gate. Comments do not count."""
    for line in job.splitlines():
        code = line.split("#", 1)[0]
        match = re.search(r"\$LASTEXITCODE\s+(-ne|-eq)\s+0\b", code)
        if match and "throw" in code and "sha256 mismatch" in code:
            return match.group(1)
    return None


def ffmpeg_sha_enforced(job: str) -> bool:
    """The hash literal is not enough. A failed verifier must throw, and -eq must not."""
    return (
        "scripts/verify_ffmpeg_zip_sha256.py" in job
        and workflow_hash_operator(job) == "-ne"
    )


def ffmpeg_exit_was_reset(job: str) -> bool:
    """True when LASTEXITCODE is set to 0 after the verifier and before the throw.

    The assignment may sit on the verifier line. The -ne throw can still be present.
    """
    codes = [line.split("#", 1)[0] for line in job.splitlines()]
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


def reset_ffmpeg_exit(job: str) -> str:
    """Mutation from the #827 verdict: zero LASTEXITCODE on the verifier line."""
    needle = "python scripts/verify_ffmpeg_zip_sha256.py --path $zip --expected $expected"
    mutated = job.replace(needle, needle + "; $LASTEXITCODE = 0", 1)
    if mutated == job:
        raise ValueError("ffmpeg verifier call was not present to reset LASTEXITCODE")
    return mutated


def windows_job_problems(job: str) -> list[str]:
    problems: list[str] = []
    for needle in (
        "runs-on: windows-latest",
        "continue-on-error: true",
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
    ):
        if needle not in job:
            problems.append(f"check-all-windows missing {needle}")
    if not ffmpeg_sha_enforced(job):
        problems.append("check-all-windows does not enforce the ffmpeg zip sha256")
    if ffmpeg_exit_was_reset(job):
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
    gate_evidence = prove_ffmpeg_hash_gate()
    print(
        "OK check-all-windows ffmpeg-sha-enforce "
        f"delete=caught operator_flip=caught exit_reset=caught credentials=caught {gate_evidence} permissions=contents:read"
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
        if PRECHECK_HELPER in text and not re.search(r"(?m)^\s*actions:\s*write\s*(?:#.*)?$", text):
            fail(f"prechecked machine writer {rel} lacks explicit actions: write permission")
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
    print(f"OK machine-writers={len(writers)} allowlisted force_push=0 unrestricted_stage=0 default_main=prechecked_exact_sha")
    for writer in writers:
        print("- " + writer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
