const { spawnSync } = require("child_process");

const logPath = process.env.INPUT_PATH;
const workspace = process.env.GITHUB_WORKSPACE;
if (!logPath || !workspace) {
  console.error("missing input path or GITHUB_WORKSPACE");
  process.exit(2);
}

const result = spawnSync("python", ["scripts/upload_gha_artifact.py", logPath], {
  cwd: workspace,
  env: process.env,
  stdio: "inherit",
});
process.exit(result.status === null ? 1 : result.status);
