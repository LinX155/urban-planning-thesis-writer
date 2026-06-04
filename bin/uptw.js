#!/usr/bin/env node

import path from "node:path";
import {
  getRepoRoot,
  getSupportedTools,
  installGlobalBundle,
  normalizeTools,
  packBundle
} from "../lib/bundle.js";

function printHelp() {
  console.log(`UPTW development CLI

Usage:
  node ./bin/uptw.js install-global [options]
  node ./bin/uptw.js pack [--out <path>]

Options:
  --tools <ids>       codex, claude, or codex,claude (default: codex,claude)
  --codex-home <path> Override CODEX_HOME for testing
  --claude-home <path> Override Claude home for testing
  --out <path>        Bundle output directory for pack (default: ./dist)
  -h, --help          Show this help

Examples:
  node ./bin/uptw.js install-global --tools codex
  node ./bin/uptw.js install-global --tools codex,claude --codex-home .\\.tmp-codex-home --claude-home .\\.tmp-claude-home
  node ./bin/uptw.js pack
`);
}

function parseArgs(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      continue;
    }
    const key = token.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      options[key] = true;
      continue;
    }
    options[key] = value;
    index += 1;
  }
  return options;
}

function printGlobalInstallSummary(results) {
  console.log("");
  console.log("Installed UPTW globally.");
  console.log("");
  for (const result of results) {
    if (result.tool === "codex") {
      console.log(`Codex`);
      console.log(`  Skills:   ${result.skillsRoot}`);
      console.log(`  Prompts:  ${result.commandsRoot}`);
      console.log(`  Commands: /UPTW-plan /UPTW-write`);
      console.log("");
      continue;
    }
    if (result.tool === "claude") {
      console.log(`Claude Code`);
      console.log(`  Skills:    ${result.skillsRoot}`);
      console.log(`  Command files: ${result.commandsRoot}`);
      console.log(`  Commands:      /UPTW-plan /UPTW-write`);
      console.log("");
    }
  }
  console.log("Restart Codex or Claude Code if it is already open.");
}

async function main() {
  const [command, ...rest] = process.argv.slice(2);

  if (!command || command === "-h" || command === "--help" || command === "help") {
    printHelp();
    return;
  }

  const options = parseArgs(rest);

  if (command === "install-global") {
    const tools = normalizeTools(options.tools ?? "codex,claude");
    const results = await installGlobalBundle({
      tools,
      codexHome: options["codex-home"],
      claudeHome: options["claude-home"]
    });
    printGlobalInstallSummary(results);
    return;
  }

  if (command === "pack") {
    const outputRoot = options.out
      ? path.resolve(options.out)
      : path.join(getRepoRoot(), "dist");
    const distRoot = await packBundle(outputRoot);
    console.log(`Packed UPTW bundle into ${distRoot}`);
    return;
  }

  throw new Error(
    `Unknown command '${command}'. Supported commands: install-global, pack. Supported tools: ${getSupportedTools().join(", ")}`
  );
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
