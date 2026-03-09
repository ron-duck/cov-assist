import Fastify from "fastify";
import helmet from "@fastify/helmet";
import cors from "@fastify/cors";
import rateLimit from "@fastify/rate-limit";
import { request } from "undici";
import { config } from "./config.js";
import { requireApiKey, enforceStreamPolicy } from "./auth.js";
import { auditLog } from "./audit.js";
import {
  IssuesTopSchema,
  IssuesCountSchema,
  IssuesSearchSchema,
  normalizeStreamName
} from "./validate.js";

const app = Fastify({ logger: { level: config.logLevel } });

await app.register(helmet, { global: true });
await app.register(cors, { origin: false });
await app.register(rateLimit, { max: 60, timeWindow: "1 minute" });

app.get("/health", async () => ({ ok: true, service: "gateway", version: "0.1.0" }));

function isTimeoutError(err) {
  return err?.name === "HeadersTimeoutError"
    || err?.name === "BodyTimeoutError"
    || err?.code === "UND_ERR_HEADERS_TIMEOUT"
    || err?.code === "UND_ERR_BODY_TIMEOUT"
    || err?.code === "ETIMEDOUT";
}

async function proxyToCore(req, reply, { method, url, body, auditAction, auditMeta = {} }) {
  try {
    const res = await request(url, {
      method,
      headers: body ? { "content-type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined
    });

    const responseBody = await res.body
      .json()
      .catch(() => ({ ok: false, error: "Upstream returned non-JSON" }));

    auditLog(req, auditAction, {
      ...auditMeta,
      statusCode: res.statusCode
    });

    reply.code(res.statusCode).send(responseBody);
  } catch (err) {
    const statusCode = isTimeoutError(err) ? 504 : 502;

    req.log.error(
      {
        err,
        upstream: url,
        method,
        auditAction
      },
      "core_request_failed"
    );

    auditLog(req, auditAction, {
      ...auditMeta,
      statusCode,
      upstreamError: err?.code || err?.name || "UNKNOWN"
    });

    reply.code(statusCode).send({
      ok: false,
      error: statusCode === 504
        ? "Core service timed out"
        : "Failed to reach core service"
    });
  }
}

app.get("/streams", { preHandler: requireApiKey }, async (req, reply) => {
  const url = `${config.coreBaseUrl}/streams`;

  await proxyToCore(req, reply, {
    method: "GET",
    url,
    auditAction: "streams_list"
  });
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

  await proxyToCore(req, reply, {
    method: "POST",
    url,
    body: { ...payload, stream },
    auditAction: "issues_top",
    auditMeta: {
      stream,
      limit: payload.limit,
      impact: payload.impact,
      status: payload.status
    }
  });
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

  await proxyToCore(req, reply, {
    method: "POST",
    url,
    body: { ...payload, stream },
    auditAction: "issues_count",
    auditMeta: {
      stream,
      impact: payload.impact,
      status: payload.status
    }
  });
});

app.post("/issues/search", { preHandler: requireApiKey }, async (req, reply) => {
  const parsed = IssuesSearchSchema.safeParse(req.body ?? {});
  if (!parsed.success) {
    reply.code(400).send({ ok: false, error: "Invalid request", details: parsed.error.flatten() });
    return;
  }

  const payload = parsed.data;
  const stream = normalizeStreamName(payload.stream);

  if (!enforceStreamPolicy(req, reply, stream)) return;

  const url = `${config.coreBaseUrl}/issues/search`;

  await proxyToCore(req, reply, {
    method: "POST",
    url,
    body: { ...payload, stream },
    auditAction: "issues_search",
    auditMeta: {
      stream,
      limit: payload.limit,
      offset: payload.offset,
      impact: payload.impact,
      status: payload.status
    }
  });
});

app.listen({ host: "0.0.0.0", port: config.port });