import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { cp, mkdir, rm, writeFile } from "node:fs/promises";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "..");

const SKILL_NAMES = ["uptw-plan", "uptw-write"];
const PUBLIC_COMMAND_FILES = ["UPTW-plan.md", "UPTW-write.md"];
const TOOL_IDS = ["codex", "claude"];
const RUNTIME_SCRIPTS = [
  "docx_state_tools.py",
  "docx_writer.py",
  "init_thesis_workspace.ps1",
  "state_memory_tools.py",
  "workspace_artifact_tools.py"
];

const PATHS = {
  templates: path.join(REPO_ROOT, "templates"),
  skillTemplates: path.join(REPO_ROOT, "templates", "skills"),
  codexPrompts: path.join(REPO_ROOT, "templates", "prompts", "codex"),
  claudeCommands: path.join(REPO_ROOT, "templates", "commands", "claude"),
  references: path.join(REPO_ROOT, "references"),
  scripts: path.join(REPO_ROOT, "scripts")
};

export function getRepoRoot() {
  return REPO_ROOT;
}

export function getSupportedTools() {
  return [...TOOL_IDS];
}

export function normalizeTools(rawTools) {
  if (!rawTools || rawTools.trim() === "" || rawTools.trim() === "all") {
    return [...TOOL_IDS];
  }

  const values = rawTools
    .split(",")
    .map((value) => value.trim().toLowerCase())
    .filter(Boolean);

  const unique = [...new Set(values)];
  const invalid = unique.filter((value) => !TOOL_IDS.includes(value));
  if (invalid.length > 0) {
    throw new Error(
      `Unsupported tool(s): ${invalid.join(", ")}. Supported values: ${TOOL_IDS.join(", ")}`
    );
  }
  return unique;
}

function resolveOptionalPath(value) {
  if (!value || value.trim() === "") {
    return null;
  }
  return path.resolve(value);
}

export function resolveCodexHome(overridePath) {
  const override = resolveOptionalPath(overridePath);
  if (override) {
    return override;
  }

  const envValue = resolveOptionalPath(process.env.CODEX_HOME);
  if (envValue) {
    return envValue;
  }

  return path.join(os.homedir(), ".codex");
}

export function resolveClaudeHome(overridePath) {
  const override = resolveOptionalPath(overridePath);
  if (override) {
    return override;
  }

  const envValue = resolveOptionalPath(process.env.UPTW_CLAUDE_HOME);
  if (envValue) {
    return envValue;
  }

  return path.join(os.homedir(), ".claude");
}

async function resetDir(targetPath) {
  await rm(targetPath, { recursive: true, force: true });
  await mkdir(targetPath, { recursive: true });
}

async function ensureDir(targetPath) {
  await mkdir(targetPath, { recursive: true });
}

async function copyRuntimeScripts(targetDir) {
  await ensureDir(targetDir);
  for (const scriptName of RUNTIME_SCRIPTS) {
    await cp(path.join(PATHS.scripts, scriptName), path.join(targetDir, scriptName));
  }
}

async function materializeSkill(skillName, targetRoot) {
  const targetDir = path.join(targetRoot, skillName);
  await rm(targetDir, { recursive: true, force: true });
  await cp(path.join(PATHS.skillTemplates, skillName), targetDir, { recursive: true });
  await cp(PATHS.references, path.join(targetDir, "references"), { recursive: true });
  await copyRuntimeScripts(path.join(targetDir, "scripts"));
}

async function copySelectedFiles(sourceDir, targetDir, fileNames) {
  await ensureDir(targetDir);
  for (const fileName of fileNames) {
    await cp(path.join(sourceDir, fileName), path.join(targetDir, fileName));
  }
}

async function installCodex({ codexHome }) {
  const skillsRoot = path.join(codexHome, "skills");
  const promptsRoot = path.join(codexHome, "prompts");

  await ensureDir(skillsRoot);
  await ensureDir(promptsRoot);

  for (const skillName of SKILL_NAMES) {
    await materializeSkill(skillName, skillsRoot);
  }

  for (const fileName of PUBLIC_COMMAND_FILES) {
    await cp(path.join(PATHS.codexPrompts, fileName), path.join(promptsRoot, fileName));
  }

  return {
    tool: "codex",
    skillsRoot,
    commandsRoot: promptsRoot
  };
}

async function installClaude({ claudeHome }) {
  const skillsRoot = path.join(claudeHome, "skills");
  const commandsRoot = path.join(claudeHome, "commands");

  await ensureDir(skillsRoot);
  await ensureDir(commandsRoot);

  for (const skillName of SKILL_NAMES) {
    await materializeSkill(skillName, skillsRoot);
  }

  for (const fileName of PUBLIC_COMMAND_FILES) {
    await cp(path.join(PATHS.claudeCommands, fileName), path.join(commandsRoot, fileName));
  }

  return {
    tool: "claude",
    skillsRoot,
    commandsRoot
  };
}

export async function installGlobalBundle({
  tools,
  codexHome,
  claudeHome
}) {
  const results = [];
  const resolvedCodexHome = resolveCodexHome(codexHome);
  const resolvedClaudeHome = resolveClaudeHome(claudeHome);

  for (const tool of tools) {
    if (tool === "codex") {
      results.push(await installCodex({ codexHome: resolvedCodexHome }));
      continue;
    }
    if (tool === "claude") {
      results.push(await installClaude({ claudeHome: resolvedClaudeHome }));
    }
  }

  return results;
}

export async function packBundle(outputRoot) {
  const distRoot = path.resolve(outputRoot || path.join(REPO_ROOT, "dist"));
  await resetDir(distRoot);

  const skillsRoot = path.join(distRoot, "skills");
  const codexPromptsRoot = path.join(distRoot, "prompts", "codex");
  const claudeCommandsRoot = path.join(distRoot, "commands", "claude");

  await ensureDir(skillsRoot);
  await ensureDir(codexPromptsRoot);
  await ensureDir(claudeCommandsRoot);

  for (const skillName of SKILL_NAMES) {
    await materializeSkill(skillName, skillsRoot);
  }

  await copySelectedFiles(PATHS.codexPrompts, codexPromptsRoot, PUBLIC_COMMAND_FILES);
  await copySelectedFiles(PATHS.claudeCommands, claudeCommandsRoot, PUBLIC_COMMAND_FILES);

  const manifest = {
    skills: [...SKILL_NAMES],
    codex_prompts: [...PUBLIC_COMMAND_FILES],
    claude_commands: [...PUBLIC_COMMAND_FILES],
    runtime_scripts: [...RUNTIME_SCRIPTS]
  };

  await writeFile(
    path.join(distRoot, "bundle-manifest.json"),
    JSON.stringify(manifest, null, 2) + "\n",
    "utf-8"
  );

  return distRoot;
}
