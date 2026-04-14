type MemoryLike = Record<string, unknown>;
type WikiLike = Record<string, unknown>;

type UnifiedHit = {
  source: "memory" | "wiki";
  id: string;
  title: string;
  normalizedScore: number;
  badges: string[];
} & Record<string, unknown>;

export function mergeSearchResults(params: {
  memory: MemoryLike[];
  wiki: WikiLike[];
  limit: number;
}): UnifiedHit[] {
  const linkedWikiPaths = new Set(
    params.wiki
      .map((item) => item.path)
      .filter((value): value is string => typeof value === "string" && value.length > 0),
  );

  const normalizedMemory: UnifiedHit[] = params.memory.map((item) => ({
    ...item,
    source: "memory",
    id: String(item.id ?? ""),
    title: String(item.title ?? ""),
    normalizedScore:
      Number(item.score ?? 0) +
      0.08 +
      (typeof item.relatedWikiPath === "string" &&
      linkedWikiPaths.has(item.relatedWikiPath)
        ? 0.12
        : 0),
    badges: ["Memory", "Canonical"],
  }));

  const normalizedWiki: UnifiedHit[] = params.wiki.map((item) => ({
    ...item,
    source: "wiki",
    id: String(item.id ?? ""),
    title: String(item.title ?? ""),
    normalizedScore: Number(item.score ?? 0),
    badges: [
      "Wiki",
      "Analyses",
      item.related_memory_id ? "Linked" : null,
    ].filter(Boolean) as string[],
  }));

  return [...normalizedMemory, ...normalizedWiki]
    .sort((a, b) => b.normalizedScore - a.normalizedScore)
    .slice(0, params.limit);
}
