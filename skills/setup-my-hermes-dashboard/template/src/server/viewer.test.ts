import { describe, expect, it } from "vitest";

import { viewerFrom } from "./viewer";

describe("viewerFrom", () => {
  it("denies administrator privileges when the gate role is missing", () => {
    expect(viewerFrom(undefined, undefined)).toEqual({ email: null, role: "member" });
    expect(viewerFrom("eve@example.com", "")).toEqual({ email: "eve@example.com", role: "member" });
  });

  it("reads the gate's user and role", () => {
    expect(viewerFrom("Ada@Example.com", "admin")).toEqual({ email: "ada@example.com", role: "admin" });
    expect(viewerFrom("bob@example.com", "member")).toEqual({ email: "bob@example.com", role: "member" });
  });

  it("treats a saved IP as a non-admin member", () => {
    expect(viewerFrom("", "user")).toEqual({ email: null, role: "member" });
  });

  it("never upgrades an unknown role", () => {
    expect(viewerFrom("eve@example.com", "owner")).toEqual({ email: "eve@example.com", role: "member" });
  });
});
