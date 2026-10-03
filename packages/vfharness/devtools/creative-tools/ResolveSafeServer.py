import asyncio
import json
import os
import sys
from pathlib import Path

SOURCE = Path(r"D:\Velvet\Tools\CreativeTools\DaVinciResolveMCP\source")
LOG = Path(r"D:\Velvet\Logs\CreativeTools\Resolve\mcp-server.log")
VELVET_ROOT = Path(r"D:\Velvet").resolve()
ACCEPTANCE_GATE = Path(r"D:\Velvet\State\CreativeTools\Resolve\acceptance.enabled")
ACCEPTANCE_ONLY = {"project_manager": {"safe_project_delete", "load", "save"}}

POLICY = {
    "project_manager": {
        "list","list_attributes","get_current","snapshot","project_capabilities",
        "probe_project_lifecycle","probe_project_settings","project_settings_snapshot",
        "database_capabilities","preset_lifecycle_probe","project_boundary_report",
        "lint","diff_to_spec","plan_spec","safe_project_create","safe_project_export",
        "safe_project_import","safe_project_archive","safe_project_restore",
        "safe_set_project_settings"
    },
    "project_settings": {
        "get_project_settings_presets","get_name","get_setting","get_unique_id",
        "get_presets","refresh_luts","get_gallery","project_summary","get_color_groups"
    },
    "media_pool": {
        "get_root_folder","get_current_folder","refresh","get_unique_id","get_selected",
        "get_clip_mattes","get_timeline_mattes","ingest_capabilities","probe_media_pool",
        "probe_ingest_item","probe_clip_properties","metadata_field_inventory",
        "check_proxy_media_compatibility","media_pool_boundary_report",
        "safe_import_media","safe_import_sequence","safe_import_folder"
    },
    "media_pool_item": {
        "get_name","get_metadata","get_third_party_metadata","get_media_id",
        "get_clip_property","get_clip_color","get_unique_id","get_transcription",
        "get_audio_mapping","get_mark_in_out","get_timeline"
    },
    "media_storage": {"get_volumes","get_subfolders","get_files"},
    "timeline": {
        "list","get_current","get_name","get_start_frame","get_end_frame",
        "get_start_timecode","get_track_count","get_track_sub_type","get_track_enabled",
        "get_track_locked","get_track_name","get_items","clip_where","story_spine_report",
        "get_setting","get_unique_id","get_media_pool_item","get_transcript",
        "get_mark_in_out","get_items_in_track","get_voice_isolation_state",
        "extract_source_frame_ranges","conform_capabilities","probe_timeline_structure",
        "detect_gaps_overlaps","source_range_report","compare_timelines",
        "detect_missing_media","build_relink_plan","conform_boundary_report",
        "audio_capabilities","probe_audio_item","probe_audio_track",
        "audio_mix_capability_report","voice_isolation_capabilities",
        "audio_mapping_report","transcription_capabilities","subtitle_generation_probe",
        "fairlight_boundary_report","export_timeline_checked","import_timeline_checked",
        "safe_set_audio_properties","safe_auto_sync_audio"
    },
    "timeline_item": {
        "get_speed","get_fades","get_type","get_output_blanking",
        "get_use_timeline_for_output_blanking","get_name","get_property","get_duration",
        "get_start","get_end","get_source_start_frame","get_source_end_frame",
        "get_source_start_time","get_source_end_time","get_left_offset","get_right_offset",
        "get_clip_enabled","get_unique_id","get_media_pool_item","get_stereo_convergence",
        "get_stereo_left_window","get_stereo_right_window","get_linked_items",
        "get_track_type_and_index","get_source_audio_mapping","get_voice_isolation_state",
        "get_retime","get_transform","get_crop","get_composite","get_audio","get_keyframes"
    },
    "render": {
        "get_audio_formats","get_audio_codecs","list_jobs","get_job_status","verify_output",
        "is_rendering","get_formats","get_codecs","get_format_and_codec","get_mode",
        "get_resolutions","get_settings","list_presets","quick_export_presets",
        "render_capabilities","validate_render_settings","quick_export_capabilities",
        "list_delivery_targets","resolve_delivery_target"
    },
    "knowledge": {"topics","get","search","capabilities"},
    "lut": {"path","list","read","capabilities"}
}

PATH_ACTIONS = {
    ("project_manager","safe_project_export"): ("path",),
    ("project_manager","safe_project_import"): ("path",),
    ("project_manager","safe_project_archive"): ("path",),
    ("project_manager","safe_project_restore"): ("path",),
    ("media_pool","safe_import_media"): ("paths",),
    ("media_pool","safe_import_sequence"): ("FilePath","file_path","pattern"),
    ("media_pool","safe_import_folder"): ("path","source_clips_path"),
    ("timeline","export_timeline_checked"): ("path",),
    ("timeline","import_timeline_checked"): ("path",),
}

os.environ["DAVINCI_RESOLVE_MCP_UPDATE_CHECK"] = "0"
os.environ["DAVINCI_RESOLVE_MCP_UPDATE_MODE"] = "never"
os.environ["RESOLVE_MCP_LOG_FILE"] = str(LOG)
os.environ["DAVINCI_RESOLVE_HEADLESS"] = "1"
LOG.parent.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SOURCE))

from src import server as upstream

def under_velvet(value):
    if value in (None, ""):
        return True
    try:
        p = Path(str(value)).expanduser().resolve()
        return p == VELVET_ROOT or VELVET_ROOT in p.parents
    except Exception:
        return False

def validate_paths(tool_name, action, params):
    fields = PATH_ACTIONS.get((tool_name, action), ())
    for field in fields:
        value = (params or {}).get(field)
        values = value if isinstance(value, list) else [value]
        for item in values:
            if item not in (None, "") and not under_velvet(item):
                raise RuntimeError(f"VelvetOS policy blocks path outside D:\\Velvet: {field}")
upstream.logger.info(
    "Result envelope mode: %s",
    upstream._apply_persisted_envelope_mode(),
)
upstream._install_threaded_tool_dispatch(upstream.mcp)

manager = getattr(upstream.mcp, "_tool_manager", None)
tools = getattr(manager, "_tools", None)
if not isinstance(tools, dict):
    raise RuntimeError("Unsupported FastMCP tool registry shape")

removed = []
for name in list(tools):
    if name not in POLICY:
        tools.pop(name)
        removed.append(name)

DISPOSABLE_PROJECT_ACTIONS = {
    "safe_project_create",
    "safe_project_export",
    "safe_project_import",
    "safe_project_archive",
    "safe_project_restore",
    "safe_project_delete",
}

def make_guard(tool_name, original, allowed):
    acceptance = ACCEPTANCE_ONLY.get(tool_name, set())
    def guarded(action: str, params=None):
        if action in acceptance:
            if not ACCEPTANCE_GATE.exists():
                raise RuntimeError(
                    f"VelvetOS acceptance gate blocks Resolve action: {tool_name}.{action}"
                )
        elif action not in allowed:
            raise RuntimeError(
                f"VelvetOS policy blocks Resolve action: {tool_name}.{action}"
            )
        p = params or {}
        if (
            tool_name == "project_manager"
            and action in DISPOSABLE_PROJECT_ACTIONS
            and bool(p.get("allow_non_mcp_name"))
        ):
            raise RuntimeError(
                "VelvetOS policy requires Resolve project names prefixed _mcp_"
            )
        validate_paths(tool_name, action, p)
        return original(action=action, params=params)
    return guarded

for name, allowed in POLICY.items():
    if name not in tools:
        raise RuntimeError(f"Required Resolve tool missing: {name}")
    tools[name].fn = make_guard(name, tools[name].fn, allowed)
async def tool_names():
    return sorted(t.name for t in await upstream.mcp.list_tools())

if "--self-test" in sys.argv:
    assert "resolve_control" not in tools
    try:
        tools["project_manager"].fn("delete", {"name":"anything"})
        raise AssertionError("blocked action unexpectedly executed")
    except RuntimeError as exc:
        assert "policy blocks" in str(exc)
    try:
        validate_paths("media_pool","safe_import_media",{"paths":[r"C:\Windows\notepad.exe"]})
        raise AssertionError("outside path unexpectedly accepted")
    except RuntimeError as exc:
        assert "outside D:\\Velvet" in str(exc)
    try:
        tools["project_manager"].fn(
            "safe_project_create",
            {"name":"anything","allow_non_mcp_name":True},
        )
        raise AssertionError("non-mcp project name unexpectedly accepted")
    except RuntimeError as exc:
        assert "prefixed _mcp_" in str(exc)
    if ACCEPTANCE_GATE.exists():
        raise AssertionError("acceptance gate must be absent during self-test")
    try:
        tools["project_manager"].fn(
            "safe_project_delete",
            {"name":"_mcp_should_not_exist"},
        )
        raise AssertionError("acceptance-only action unexpectedly accepted")
    except RuntimeError as exc:
        assert "acceptance gate blocks" in str(exc)
    print(json.dumps({
        "ok": True,
        "tool_count": len(tools),
        "removed_count": len(removed),
        "blocked_action_test": True,
        "path_gate_test": True,
        "project_name_gate_test": True,
        "acceptance_gate_test": True,
    }))
    raise SystemExit(0)

if "--list-tools" in sys.argv:
    names = asyncio.run(tool_names())
    print(json.dumps({
        "ok": True,
        "upstream_version": upstream.VERSION,
        "removed": sorted(removed),
        "tool_count": len(names),
        "tools": names,
        "policy": {k: sorted(v) for k, v in sorted(POLICY.items())},
    }))
    raise SystemExit(0)

upstream.logger.info(
    "VelvetOS safe Resolve surface: tools=%d removed=%d",
    len(tools), len(removed)
)
upstream.logger.info(
    "Starting VelvetOS DaVinci Resolve MCP safe stdio server with %d tools",
    len(asyncio.run(tool_names())),
)
upstream.run_fastmcp_stdio(upstream.mcp)
