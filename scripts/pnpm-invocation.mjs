import { existsSync } from "node:fs";

// Windows refuses to spawn .cmd shims without a shell (Node >= 20), so pnpm must be
// reached through its JavaScript entry. These scripts are always launched by pnpm
// itself, which exposes that entry as npm_execpath. POSIX keeps the historical PATH lookup.
export function pnpmInvocation(env = process.env) {
  if (process.platform !== "win32") return { command: "pnpm", prefixArgs: [] };
  const entry = env.npm_execpath;
  if (!entry || !existsSync(entry))
    throw new Error(
      "Windows requires running this script through pnpm (missing npm_execpath). Use the pnpm <task> entry instead of invoking node directly.",
    );
  return { command: process.execPath, prefixArgs: [entry] };
}
