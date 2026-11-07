import { KeyboardEvent, useEffect, useRef, useState } from "react";

import { SendIcon, StopIcon } from "./Icons";

interface ComposerProps {
  placeholder: string;
  busy: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
}

export function Composer({ placeholder, busy, onSend, onStop }: ComposerProps) {
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const ready = draft.trim().length >= 3;

  useEffect(() => {
    const input = inputRef.current;
    if (!input) return;
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
  }, [draft]);

  function send() {
    if (!ready || busy) return;
    onSend(draft.trim());
    setDraft("");
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  }

  return (
    <div className="composer-wrap">
      <div className="composer">
        <label htmlFor="question" className="visually-hidden">
          Your question
        </label>
        <textarea
          id="question"
          ref={inputRef}
          rows={1}
          value={draft}
          maxLength={500}
          placeholder={placeholder}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
          autoFocus
        />
        {busy ? (
          <button type="button" className="round-button stop" onClick={onStop} aria-label="Stop">
            <StopIcon />
          </button>
        ) : (
          <button
            type="button"
            className="round-button"
            onClick={send}
            disabled={!ready}
            aria-label="Send"
          >
            <SendIcon />
          </button>
        )}
      </div>
      <p className="disclaimer">
        Sheria can make mistakes and is not professional advice. Confirm important details with the
        agency.
      </p>
    </div>
  );
}
