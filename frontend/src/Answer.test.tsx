import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Answer, Sources } from "./Answer";
import { Passage } from "./chat";

const source = (title: string): Passage => ({
  id: 1,
  agency: "KRA",
  title,
  url: `https://x.test/${title}`,
  heading: "",
  content: `${title} text`,
});

describe("Answer", () => {
  it("links a citation to its source", () => {
    const html = renderToStaticMarkup(<Answer turnId={2} text="Due by the 9th [1]." sourceCount={1} />);
    expect(html).toContain('href="#turn-2-source-1"');
  });

  it("leaves a citation with no matching source as plain text", () => {
    const html = renderToStaticMarkup(<Answer turnId={0} text="Invented [7]." sourceCount={1} />);
    expect(html).not.toContain("<a");
    expect(html).toContain("[7]");
  });
});

describe("Sources", () => {
  const sources = [source("PAYE"), source("VAT"), source("Rent")];

  it("shows only cited passages and keeps their numbers", () => {
    const html = renderToStaticMarkup(
      <Sources turnId={0} sources={sources} cited={[3]} expanded={false} />,
    );
    expect(html).toContain("Rent");
    expect(html).not.toContain("PAYE");
    expect(html).toContain('value="3"');
  });

  it("renders nothing when nothing was cited", () => {
    const html = renderToStaticMarkup(
      <Sources turnId={0} sources={sources} cited={[]} expanded={false} />,
    );
    expect(html).toBe("");
  });

  it("opens passages when they are the whole answer", () => {
    const html = renderToStaticMarkup(
      <Sources turnId={0} sources={sources} cited={[1]} expanded={true} />,
    );
    expect(html).toContain("<details open");
  });
});
