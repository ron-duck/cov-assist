import Fastify from "fastify";
import helmet from "@fastify/helmet";
import cors from "@fastify/cors";
import rateLimit from "@fastify/rate-limit";
import { request } from "undici";
import { config } from "./config.js";
import { requireApiKey, enforceStreamPolicy } from "./auth.js";
import { auditLog } from "./audit.js";
import { IssuesTopSchema, IssuesCountSchema, normalizeStreamName } from "./validate.js";

const app = Fastify({ logger: { level: config.logLevel } });

await app.register(helmet, { global: true });
await app.register(cors, { origin: false });
await app.register(rateLimit, { max: 60, timeWindow: "1 minute" });

app.get("/health", async () => ({ ok: true, service: "gateway", version: "0.1.0" }));

app.get("/streams", { preHandler: requireApiKey }, async (req, reply) => {
  const url = `${config.coreBaseUrl}/streams`;
  const res = await request(url, { method: "GET" });
  const body = await res.body.json();
  auditLog(req, "streams_list", { statusCode: res.statusCode });
  reply.code(res.statusCode).send(body);
});

app.post("/issues/top", { preHandler: requireApiKey }, async (req, reply) => {
  const parsed = IssuesTopSchema.safeParse(req.body ?? {});
  if (!parsed.success) {
    reply.code(400).send({ ok: false, error: "Invalid request", details: parsed.error.flatten() });
    return;
  }

  const payload = parsed.data;
  const stream = normalizeStreamName(payload.stream);

  if (!enforceStreamPolicy(req, reply, stream)) return;

  const url = `${config.coreBaseUrl}/issues/top`;
  const res = await request(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ ...payload, stream })
  });

  const body = await res.body.json().catch(() => ({ ok: false, error: "Upstream returned non-JSON" }));
  auditLog(req, "issues_top", {
    stream,
    statusCode: res.statusCode,
    limit: payload.limit,
    impact: payload.impact,
    status: payload.status,
    returned: body?.total_returned
  });

  reply.code(res.statusCode).send(body);
});

app.post("/issues/count", { preHandler: requireApiKey }, async (req, reply) => {
  const parsed = IssuesCountSchema.safeParse(req.body ?? {});
  if (!parsed.success) {
    reply.code(400).send({ ok: false, error: "Invalid request", details: parsed.error.flatten() });
    return;
  }

  const payload = parsed.data;
  const stream = normalizeStreamName(payload.stream);

  if (!enforceStreamPolicy(req, reply, stream)) return;

  const url = `${config.coreBaseUrl}/issues/count`;
  const res = await request(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ ...payload, stream })
  });

  const body = await res.body.json().catch(() => ({ ok: false, error: "Upstream returned non-JSON" }));
  auditLog(req, "issues_count", {
    stream,
    statusCode: res.statusCode,
    impact: payload.impact,
    status: payload.status,
    count: body?.count
  });

  reply.code(res.statusCode).send(body);
});

app.listen({ host: "0.0.0.0", port: config.port });
