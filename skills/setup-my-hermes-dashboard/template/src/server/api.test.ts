import { describe, expect, it } from "vitest";

import { readJson } from "./api";

describe("readJson", () => {
  it("accepts a valid small JSON request", async () => {
    const req = new Request("http://localhost/api", { method: "POST", body: '{"ok":true}' });
    expect(await readJson(req, 64)).toEqual({ ok: true });
  });

  it("rejects bodies above the byte limit, including multibyte characters", async () => {
    const req = new Request("http://localhost/api", { method: "POST", body: JSON.stringify({ value: "é".repeat(20) }) });
    expect(await readJson(req, 20)).toBeNull();
  });

  it("rejects invalid JSON and empty bodies", async () => {
    expect(await readJson(new Request("http://localhost/api", { method: "POST", body: "{" }), 100)).toBeNull();
    expect(await readJson(new Request("http://localhost/api"), 100)).toBeNull();
  });

  it("stops consuming a streaming body when its byte limit is exceeded", async () => {
    let reads = 0;
    const body = new ReadableStream<Uint8Array>({
      pull(controller) {
        reads += 1;
        controller.enqueue(new Uint8Array(32));
        if (reads > 10) controller.close();
      },
    });
    const req = new Request("http://localhost/api", { method: "POST", body, duplex: "half" } as RequestInit & { duplex: "half" });
    expect(await readJson(req, 40)).toBeNull();
    expect(reads).toBeLessThan(11);
  });
});
