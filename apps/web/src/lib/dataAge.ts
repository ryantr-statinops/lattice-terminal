export function isDataOlderThan(
  timestamp: string | null | undefined,
  maxAgeMs: number,
  now = Date.now(),
): boolean {
  if (!timestamp) return false;
  const time = Date.parse(timestamp);
  return Number.isFinite(time) && now - time > maxAgeMs;
}
