import { z } from "zod";

export const IssuesTopSchema = z.object({
  stream: z.string().min(1).max(200),
  status: z.array(z.string().min(1).max(50)).optional(),
  impact: z.array(z.string().min(1).max(50)).optional(),
  limit: z.number().int().min(1).max(200).default(20)
});

export const IssuesCountSchema = z.object({
  stream: z.string().min(1).max(200),
  status: z.array(z.string().min(1).max(50)).optional(),
  impact: z.array(z.string().min(1).max(50)).optional()
});

export const IssuesSearchSchema = z.object({
  stream: z.string().min(1).max(200),
  status: z.array(z.string().min(1).max(50)).optional(),
  impact: z.array(z.string().min(1).max(50)).optional(),
  limit: z.number().int().min(1).max(200).default(20),
  offset: z.number().int().min(0).default(0)
});

export const IssueDetailsSchema = z.object({
  cid: z.string().min(1),
  stream: z.string().min(1).max(200)
});

export function normalizeStreamName(s) {
  return s.trim();
}
