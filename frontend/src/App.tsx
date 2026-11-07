import { useEffect, useRef, useState } from "react";

import { askQuestion, ChatEvent, FieldId } from "./chat";
import { Composer } from "./Composer";
import { FIELDS, fieldById } from "./fields";
import { ChatIcon, CloseIcon, FieldIcon, Logo, MenuIcon, PlusIcon } from "./Icons";
import { ChatMessage, Message } from "./Message";
import { FieldPicker, FieldStart } from "./Welcome";

interface Chat {
  id: number;
  field: FieldId;
  title: string;
  messages: ChatMessage[];
}

const SERVER_ERROR = "Could not reach the server. Please try again.";
let nextId = 1;

function applyEvent(message: ChatMessage, event: ChatEvent): ChatMessage {
  switch (event.event) {
    case "delta":
      return { ...message, text: message.text + event.data.text };
    case "done":
      return { ...message, streaming: false };
    case "error":
      return { ...message, error: event.data.message, streaming: false };
  }
}

export function App() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [field, setField] = useState<FieldId | null>(null);
  const [busy, setBusy] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const active = chats.find((chat) => chat.id === activeId) ?? null;

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: "end" });
  }, [active?.messages]);

  function updateMessage(chatId: number, messageId: number, change: (m: ChatMessage) => ChatMessage) {
    setChats((all) =>
      all.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              messages: chat.messages.map((m) => (m.id === messageId ? change(m) : m)),
            }
          : chat,
      ),
    );
  }

  async function send(question: string) {
    if (busy || !field) return;
    const user: ChatMessage = { id: nextId++, role: "user", text: question };
    const reply: ChatMessage = { id: nextId++, role: "assistant", text: "", streaming: true };
    const chatId = active?.id ?? nextId++;
    setChats((all) =>
      active
        ? all.map((chat) =>
            chat.id === chatId ? { ...chat, messages: [...chat.messages, user, reply] } : chat,
          )
        : [{ id: chatId, field, title: question, messages: [user, reply] }, ...all],
    );
    setActiveId(chatId);
    setBusy(true);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await askQuestion(
        question,
        field,
        (event) => updateMessage(chatId, reply.id, (m) => applyEvent(m, event)),
        controller.signal,
      );
      updateMessage(chatId, reply.id, (m) => ({ ...m, streaming: false }));
    } catch {
      const stopped = controller.signal.aborted;
      updateMessage(chatId, reply.id, (m) => ({
        ...m,
        streaming: false,
        text: stopped && !m.text ? "Stopped." : m.text,
        error: stopped ? undefined : SERVER_ERROR,
      }));
    } finally {
      setBusy(false);
    }
  }

  function startNew(nextField: FieldId | null) {
    abortRef.current?.abort();
    setActiveId(null);
    setField(nextField);
    setMenuOpen(false);
  }

  function openChat(chat: Chat) {
    setActiveId(chat.id);
    setField(chat.field);
    setMenuOpen(false);
  }

  return (
    <div className="app">
      <div className="flag-stripe" aria-hidden="true" />
      {menuOpen && (
        <button
          type="button"
          className="scrim"
          aria-label="Close menu"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <div className="brand">
          <Logo />
          <span>Sheria</span>
          <button
            type="button"
            className="icon-button menu-close"
            aria-label="Close menu"
            onClick={() => setMenuOpen(false)}
          >
            <CloseIcon />
          </button>
        </div>

        <button type="button" className="new-chat" onClick={() => startNew(null)}>
          <PlusIcon /> New chat
        </button>

        <nav aria-label="Topics">
          <h2>Topics</h2>
          {FIELDS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`side-item ${field === item.id ? "current" : ""}`}
              aria-current={field === item.id ? "true" : undefined}
              onClick={() => startNew(item.id)}
            >
              <FieldIcon field={item.id} /> {item.name}
            </button>
          ))}
        </nav>

        {chats.length > 0 && (
          <nav className="history" aria-label="Chats">
            <h2>Chats</h2>
            {chats.map((chat) => (
              <button
                key={chat.id}
                type="button"
                className={`side-item ${chat.id === activeId ? "current" : ""}`}
                onClick={() => openChat(chat)}
              >
                <ChatIcon /> <span className="side-title">{chat.title}</span>
              </button>
            ))}
          </nav>
        )}
      </aside>

      <main className="main">
        <header className="topbar">
          <button
            type="button"
            className="icon-button menu-open"
            aria-label="Open menu"
            onClick={() => setMenuOpen(true)}
          >
            <MenuIcon />
          </button>
          {field && (
            <span className="topic">
              <FieldIcon field={field} /> {fieldById(field).name}
            </span>
          )}
        </header>

        <div className="scroll">
          {!field && <FieldPicker onPick={(picked) => startNew(picked)} />}
          {field && !active && <FieldStart field={field} onAsk={(q) => void send(q)} />}
          {active && (
            <div className="thread" aria-live="polite">
              {active.messages.map((message) => (
                <Message key={message.id} message={message} />
              ))}
              <div ref={endRef} />
            </div>
          )}
        </div>

        {field && (
          <Composer
            placeholder={fieldById(field).placeholder}
            busy={busy}
            onSend={(text) => void send(text)}
            onStop={() => abortRef.current?.abort()}
          />
        )}
      </main>
    </div>
  );
}
