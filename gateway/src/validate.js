import { z } from "zod";

export const IssuesTopSchema = z.object({
  stream: z.string().min(1).max(200),
  status: z.array(z.string().min(1).max(50)).default(["New"]),
  impact: z.array(z.string().min(1).max(50)).default(["High"]),
  limit: z.number().int().min(1).max(200).default(20)
});

export const IssuesCountSchema = z.object({
  stream: z.string().min(1).max(200),
  status: z.array(z.string().min(1).max(50)).default(["New"]),
  impact: z.array(z.string().min(1).max(50)).default(["High"])
});

export function normalizeStreamName(s) {
  return s.trim();
}
