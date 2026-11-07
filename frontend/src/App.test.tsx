import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { App } from "./App";
import { FIELDS } from "./fields";
import { Message } from "./Message";
import { FieldPicker, FieldStart } from "./Welcome";

const noop = () => undefined;

describe("the first screen", () => {
  const html = renderToStaticMarkup(<App />);

  it("asks the user to choose a topic", () => {
    expect(html).toContain("What do you need help with?");
  });

  it("has no question box until a topic is chosen", () => {
    expect(html).not.toContain("<textarea");
  });
});

describe("FieldPicker", () => {
  it("offers every field", () => {
    const html = renderToStaticMarkup(<FieldPicker onPick={noop} />);
    for (const field of FIELDS) expect(html).toContain(field.name);
  });
});

describe("FieldStart", () => {
  it("suggests questions for the chosen field", () => {
    const html = renderToStaticMarkup(<FieldStart field="helb" onAsk={noop} />);
    expect(html).toContain("When do I start repaying my HELB loan?");
    expect(html).not.toContain("VAT");
  });
});

describe("Message", () => {
  it("renders lists in an answer", () => {
    const text = "Follow these steps:\n\n1. Log in\n2. Pay";
    const html = renderToStaticMarkup(
      <Message message={{ id: 1, role: "assistant", text }} />,
    );
    expect(html).toContain("<ol>");
  });

  it("shows typing dots before the first words arrive", () => {
    const html = renderToStaticMarkup(
      <Message message={{ id: 1, role: "assistant", text: "", streaming: true }} />,
    );
    expect(html).toContain('class="typing"');
  });

  it("shows the error when an answer fails", () => {
    const html = renderToStaticMarkup(
      <Message message={{ id: 1, role: "assistant", text: "", error: "Try again" }} />,
    );
    expect(html).toContain("Try again");
    expect(html).toContain('role="alert"');
  });

  it("does not render HTML sent in an answer", () => {
    const html = renderToStaticMarkup(
      <Message message={{ id: 1, role: "assistant", text: "<img src=x onerror=alert(1)>" }} />,
    );
    expect(html).not.toContain("<img");
  });
});
