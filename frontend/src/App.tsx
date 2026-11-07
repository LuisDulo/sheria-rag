import { FormEvent, useEffect, useRef, useState } from "react";

import { askQuestion, ChatEvent, Passage } from "./chat";

interface Turn {
  question: string;
  sources: Passage[];
  answer: string;
  cited: number[];
  notice?: string;
  error?: string;
  finished: boolean;
}

const EXAMPLES = [
  "When must employers remit PAYE?",
  "How much tax do landlords pay on rent?",
  "When do I start repaying my HELB loan?",
  "How do I register for SHA?",
];

function applyEvent(turn: Turn, event: ChatEvent): Turn {
  switch (event.event) {
    case "sources":
      return { ...turn, sources: event.data };
    case "delta":
      return { ...turn, answer: turn.answer + event.data.text };
    case "notice":
      return { ...turn, notice: event.data.message };
    case "done":
      return { ...turn, cited: event.data.cited, finished: true };
    case "error":
      return { ...turn, error: event.data.message, finished: true };
  }
}

export function App() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [turns]);

  const updateLast = (change: (turn: Turn) => Turn) =>
    setTurns((all) => [...all.slice(0, -1), change(all[all.length - 1])]);

  async function send(question: string) {
    const text = question.trim();
    if (text.length < 3 || busy) return;
    setBusy(true);
    setDraft("");
    setTurns((all) => [
      ...all,
      { question: text, sources: [], answer: "", cited: [], finished: false },
    ]);
    try {
      await askQuestion(text, (event) => updateLast((turn) => applyEvent(turn, event)));
    } catch {
      updateLast((turn) => ({
        ...turn,
        error: "Could not reach the server. Please try again.",
        finished: true,
      }));
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void send(draft);
  }

  return (
    <div className="page">
      <header className="masthead">
        <h1>Sheria</h1>
        <p>Answers on Kenyan tax, SHA and HELB rules, drawn from official guidance.</p>
      </header>

      <main className="thread" aria-live="polite">
        {turns.length === 0 && (
          <section className="empty">
            <h2>Try asking</h2>
            <div className="examples">
              {EXAMPLES.map((example) => (
                <button key={example} type="button" onClick={() => void send(example)}>
                  {example}
                </button>
              ))}
            </div>
          </section>
        )}

        {turns.map((turn, index) => (
          <article className="turn" key={index}>
            <h2 className="question">{turn.question}</h2>
            {!turn.finished && !turn.answer && <p className="status">Searching official pages…</p>}
            {turn.answer && <p className="answer">{turn.answer}</p>}
            {turn.notice && <p className="status">{turn.notice}</p>}
            {turn.error && (
              <p className="error" role="alert">
                {turn.error}
              </p>
            )}
          </article>
        ))}
        <div ref={endRef} />
      </main>

      <form className="composer" onSubmit={onSubmit}>
        <label htmlFor="question" className="visually-hidden">
          Your question
        </label>
        <input
          id="question"
          value={draft}
          maxLength={500}
          placeholder="Ask about PAYE, VAT, SHA or your HELB loan"
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit" disabled={busy || draft.trim().length < 3}>
          Ask
        </button>
      </form>
    </div>
  );
}
