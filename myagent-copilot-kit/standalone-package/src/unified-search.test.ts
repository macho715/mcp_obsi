import assert from "node:assert/strict";
import test from "node:test";

import { mergeSearchResults } from "./unified-search.js";

test("mergeSearchResults keeps source labels and memory priority", () => {
  const result = mergeSearchResults({
    memory: [
      {
        source: "memory",
        id: "MEM-1",
        title: "KB: SHU issue pointer",
        score: 0.8,
        fetchRoute: "fetch",
        relatedWikiPath: "wiki/analyses/logistics_issue_shu_2025-11-26_3.md",
      },
    ],
    wiki: [
      {
        source: "wiki",
        id: "wiki:analyses/logistics_issue_shu_2025-11-26_3",
        title: "[SHU Issue] 2025-11-26 Event #3",
        score: 0.9,
        fetchRoute: "fetch_wiki",
        path: "wiki/analyses/logistics_issue_shu_2025-11-26_3.md",
        related_memory_id: "MEM-1",
      },
    ],
    limit: 5,
  });

  assert.equal(result[0].source, "memory");
  assert.equal(result[1].source, "wiki");
  assert.equal(result[1].badges.includes("Linked"), true);
});
