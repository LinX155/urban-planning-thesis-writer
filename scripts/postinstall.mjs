import { installGlobalBundle, normalizeTools } from "../lib/bundle.js";

if (process.env.CI === "true" || process.env.CI === "1") {
  process.exit(0);
}

if (process.env.UPTW_NO_GLOBAL_INSTALL === "1") {
  process.exit(0);
}

function isGlobalInstall() {
  const npmGlobal = String(process.env.npm_config_global || "").toLowerCase();
  const npmLocation = String(process.env.npm_config_location || "").toLowerCase();
  return npmGlobal === "true" || npmGlobal === "1" || npmLocation === "global";
}

if (!isGlobalInstall()) {
  process.exit(0);
}

try {
  const tools = normalizeTools(process.env.UPTW_TOOLS ?? "codex,claude");
  const results = await installGlobalBundle({ tools });

  console.log("");
  console.log("UPTW installed globally.");
  console.log("");

  for (const result of results) {
    if (result.tool === "codex") {
      console.log("Codex");
      console.log(`  Skills:   ${result.skillsRoot}`);
      console.log(`  Prompts:  ${result.commandsRoot}`);
      console.log(`  Commands: /UPTW-init /UPTW-plan /UPTW-write`);
      console.log("");
      continue;
    }

    if (result.tool === "claude") {
      console.log("Claude Code");
      console.log(`  Skills:   ${result.skillsRoot}`);
      console.log(`  Command files: ${result.commandsRoot}`);
      console.log(`  Commands: /UPTW-init /UPTW-plan /UPTW-write`);
      console.log("");
    }
  }

  console.log("Restart Codex or Claude Code if it is already open.");
  console.log("");
} catch (error) {
  console.log("");
  console.log("UPTW global registration was skipped.");
  console.log(`Reason: ${error instanceof Error ? error.message : String(error)}`);
  console.log("You can retry by reinstalling globally after fixing the environment.");
  console.log("");
  process.exit(0);
}
