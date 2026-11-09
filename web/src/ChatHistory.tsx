import React from "react";
import {MessageSquare, Trash2} from "lucide-react";

export type Conversation = {
  sessionId: string;
  title: string;
  createdAt: number;
  updatedAt: number;
};

type Props = {
  conversations: Conversation[];
  activeSession: string | null;
  loading: boolean;
  disabled: boolean;
  onOpen: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
};

export default function ChatHistory({conversations, activeSession, loading, disabled, onOpen, onDelete}: Props) {
  return (
    <div className="history">
      <div className="section history-title">RECENT CHATS</div>
      {loading && <p className="history-empty">Loading conversations...</p>}
      {!loading && conversations.length === 0 && (
        <p className="history-empty">Your conversations will appear here.</p>
      )}
      <div className="history-list">
        {conversations.map(item => (
          <div className={"history-item " + (activeSession === item.sessionId ? "selected" : "")} key={item.sessionId}>
            <button
              type="button"
              className="history-open"
              disabled={disabled}
              onClick={() => onOpen(item.sessionId)}
              title={item.title}
            >
              <MessageSquare size={15} />
              <span>{item.title || "New conversation"}</span>
            </button>
            <button
              type="button"
              className="history-delete"
              disabled={disabled}
              aria-label={"Delete " + item.title}
              title="Delete conversation"
              onClick={() => onDelete(item.sessionId)}
            >
              <Trash2 size={15} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
