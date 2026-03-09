import crypto from "crypto";
import { config } from "./config.js";

function timingSafeEqualStr(a, b) {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ab.length !== bb.length) return false;
  return crypto.timingSafeEqual(ab, bb);
}

export function requireApiKey(req, reply, done) {
  const key = req.headers["x-api-key"];
  if (!key || typeof key !== "string") {
    reply.code(401).send({ ok: false, error: "Missing X-API-Key" });
    return;
  }

  const allowed = config.apiKeys.some(k => timingSafeEqualStr(k, key));
  if (!allowed) {
    reply.code(403).send({ ok: false, error: "Invalid API key" });
    return;
  }

  req.apiKey = key;
  done();
}

export function enforceStreamPolicy(req, reply, streamName) {
  const pol = config.keyPolicy?.[req.apiKey];
  if (!pol || !pol.streams || pol.streams.length === 0) return true;
  if (pol.streams.includes("*")) return true;
  if (!pol.streams.includes(streamName)) {
    reply.code(403).send({ ok: false, error: `API key not permitted for stream: ${streamName}` });
    return false;
  }
  return true;
}
