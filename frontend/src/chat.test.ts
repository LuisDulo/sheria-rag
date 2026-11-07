import { describe, expect, it } from "vitest";

import { parseEvents } from "./chat";

describe("parseEvents", () => {
  it("reads complete events", () => {
    const { events, rest } = parseEvents('event: delta\ndata: {"text":"Hi"}\n\n');
    expect(events).toEqual([{ event: "delta", data: { text: "Hi" } }]);
    expect(rest).toBe("");
  });

  it("keeps a partial event for the next read", () => {
    const first = parseEvents('event: delta\ndata: {"text":"A"}\n\nevent: del');
    expect(first.events).toHaveLength(1);
    expect(first.rest).toBe("event: del");

    const second = parseEvents(first.rest + 'ta\ndata: {"text":"B"}\n\n');
    expect(second.events).toEqual([{ event: "delta", data: { text: "B" } }]);
  });

  it("keeps blank lines inside the JSON text", () => {
    const { events } = parseEvents('event: delta\ndata: {"text":"a\\n\\nb"}\n\n');
    expect(events[0]).toEqual({ event: "delta", data: { text: "a\n\nb" } });
  });
});
