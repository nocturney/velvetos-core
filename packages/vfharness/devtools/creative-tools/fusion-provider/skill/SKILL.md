---
name: fusion-native-bridge
description: >-
  Infrastructure adapter for Autodesk Fusion. Exposes bounded VelvetOS tools
  backed by Autodesk Fusion's built-in localhost MCP server. This is a transport
  integration surface, not a creative workflow skill.
license: MIT
metadata:
  dcc-mcp:
    dcc: fusion
    version: "0.1.0"
    layer: infrastructure
    search-hint: "fusion autodesk status connectivity native mcp health active command"
    tags: "fusion, autodesk, native-mcp, infrastructure, adapter"
    tools: tools.yaml
---

# Fusion Native Bridge

Bounded production adapter between the existing DCC-MCP gateway and Autodesk
Fusion's built-in local MCP endpoint at `127.0.0.1:27182`.

The adapter never exposes Autodesk's arbitrary-script tool directly. Higher
layers receive only explicitly declared typed tools.

## Verification

After every bounded operation, verify the returned Fusion readback or exact exported artifact before reporting success. For exports, require the expected file to exist and record its SHA-256. For connectivity/status operations, require the native MCP endpoint and the current Update Sentinel routing gate to be healthy. Treat a missing readback, artifact, hash, or healthy gate as a failed operation; never infer success from launch state alone.
