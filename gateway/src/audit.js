export function auditLog(req, action, meta) {
  const entry = {
    ts: new Date().toISOString(),
    ip: req.ip,
    apiKeySuffix: typeof req.apiKey === "string" ? req.apiKey.slice(-6) : undefined,
    action,
    ...meta
  };
  req.log.info(entry, "audit");
}
