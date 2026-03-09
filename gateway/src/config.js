export function getEnv(name, def = undefined) {
  const v = process.env[name];
  return (v === undefined || v === "") ? def : v;
}

export function parseJsonEnv(name, defObj) {
  const raw = getEnv(name, null);
  if (!raw) return defObj;
  try { return JSON.parse(raw); } catch { return defObj; }
}

export const config = {
  port: Number(getEnv("GATEWAY_PORT", "8080")),
  apiKeys: String(getEnv("GATEWAY_API_KEYS", "")).split(",").map(s => s.trim()).filter(Boolean),
  keyPolicy: parseJsonEnv("GATEWAY_KEY_POLICY_JSON", {}),
  coreBaseUrl: String(getEnv("CORE_BASE_URL", "http://core:8000")).replace(/\/$/, ""),
  logLevel: String(getEnv("LOG_LEVEL", "INFO")).toLowerCase()
};
