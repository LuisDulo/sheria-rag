import { Passage } from "./chat";

interface AnswerProps {
  turnId: number;
  text: string;
  sourceCount: number;
}

export function sourceAnchor(turnId: number, number: number): string {
  return `turn-${turnId}-source-${number}`;
}

/** Turns [1] into a link to its source. A number with no matching source stays plain text. */
export function Answer({ turnId, text, sourceCount }: AnswerProps) {
  return (
    <p className="answer">
      {text.split(/(\[\d+\])/).map((part, index) => {
        const number = Number(part.match(/^\[(\d+)\]$/)?.[1]);
        if (number >= 1 && number <= sourceCount) {
          return (
            <a
              key={index}
              className="citation"
              href={`#${sourceAnchor(turnId, number)}`}
              aria-label={`Source ${number}`}
            >
              {number}
            </a>
          );
        }
        return part;
      })}
    </p>
  );
}

interface SourcesProps {
  turnId: number;
  sources: Passage[];
  cited: number[];
  expanded: boolean;
}

/** Lists only the passages the answer relied on, keeping the numbers used in the text. */
export function Sources({ turnId, sources, cited, expanded }: SourcesProps) {
  if (cited.length === 0) return null;
  const ordered = [...cited].sort((a, b) => a - b);
  return (
    <section className="sources" aria-label="Sources">
      <h3>Sources</h3>
      <ol>
        {ordered.map((number) => {
          const source = sources[number - 1];
          return (
            <li key={number} id={sourceAnchor(turnId, number)} value={number}>
              <a href={source.url} target="_blank" rel="noopener noreferrer">
                {source.agency}: {source.title}
              </a>
              {source.heading && <span className="section"> {source.heading}</span>}
              <details open={expanded}>
                <summary>Passage</summary>
                <blockquote>{source.content}</blockquote>
              </details>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
