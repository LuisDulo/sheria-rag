import { useState } from "react";
import Markdown from "react-markdown";

import { AlertIcon, CheckIcon, CopyIcon, Logo } from "./Icons";

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  text: string;
  error?: string;
  streaming?: boolean;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button type="button" className="icon-button" onClick={() => void copy()} aria-label="Copy answer">
      {copied ? <CheckIcon /> : <CopyIcon />}
    </button>
  );
}

export function Message({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="message message-user">
        <p>{message.text}</p>
      </div>
    );
  }

  return (
    <div className="message message-assistant">
      <span className="avatar">
        <Logo size={22} />
      </span>
      <div className="message-body">
        {message.streaming && !message.text && (
          <span className="typing" role="status" aria-label="Thinking">
            <i />
            <i />
            <i />
          </span>
        )}
        {message.text && (
          <div className="answer">
            <Markdown>{message.text}</Markdown>
          </div>
        )}
        {message.error && (
          <p className="error" role="alert">
            <AlertIcon /> {message.error}
          </p>
        )}
        {message.text && !message.streaming && (
          <div className="message-actions">
            <CopyButton text={message.text} />
          </div>
        )}
      </div>
    </div>
  );
}
