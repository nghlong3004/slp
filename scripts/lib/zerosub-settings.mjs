// Write through Paseo's settings RPC so its schema and revision checks apply.
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

export async function applyPreferences(client, desired) {
  const state = await client.invokePluginRpc("zerosub", "settings.preferences.read", {});
  if (state.status !== "ready") throw new Error("ZeroSub preferences are not ready");
  for (const key of Object.keys(desired)) {
    if (!(key in state.values)) throw new Error(`Installed ZeroSub does not expose expected setting: ${key}`);
  }
  const result = await client.invokePluginRpc("zerosub", "settings.preferences.write", {
    revision: state.revision,
    values: { ...state.values, ...desired },
  });
  if (result.status !== "saved") throw new Error(`ZeroSub rejected preferences: ${result.error ?? result.status}`);
  for (const [key, value] of Object.entries(desired)) {
    if (result.values[key] !== value) throw new Error(`ZeroSub did not retain setting: ${key}`);
  }
  return result.values;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const [cliRoot, home, preferenceFile] = process.argv.slice(2);
  let client;
  try {
    const { connectToDaemon } = await import(pathToFileURL(path.join(cliRoot, "dist/utils/client.js")));
    client = await connectToDaemon({ target: { kind: "instance", home }, timeout: 10000 });
    await applyPreferences(client, JSON.parse(fs.readFileSync(preferenceFile, "utf8")));
    process.stdout.write("ZeroSub preferences saved through the live schema: automatic switching on; automatic reset spending and cross-provider fork off.\n");
  } catch (error) {
    process.stderr.write(`ZeroSub settings: ${error.message}\n`);
    process.exitCode = 1;
  } finally {
    await client?.close();
  }
}
