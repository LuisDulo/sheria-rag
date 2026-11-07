export type FieldId = "tax" | "sha" | "helb";

export type ChatEvent =
  | { event: "delta"; data: { text: string } }
  | { event: "done"; data: Record<string, never> }
  | { event: "error"; data: { message: string } };

/** Split a buffer into complete server-sent events, returning whatever is left over. */
export function parseEvents(buffer: string): { events: ChatEvent[]; rest: string } {
  const blocks = buffer.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events = blocks.map((block) => {
    const [eventLine, dataLine] = block.split("\n");
    return {
      event: eventLine.replace("event: ", ""),
      data: JSON.parse(dataLine.replace("data: ", "")),
    } as ChatEvent;
  });
  return { events, rest };
}

export async function askQuestion(
  question: string,
  field: FieldId,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, field }),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) return;
    const { events, rest } = parseEvents(buffer + value);
    buffer = rest;
    events.forEach(onEvent);
  }
}
