"use client";

import { Copy, Paperclip, Send, ThumbsDown, ThumbsUp, X } from "lucide-react";
import { useRef, useState } from "react";

import type { Message, UploadedFile } from "@/lib/api";

interface ChatMessageProps {
  message: Message;
}

function formatContent(content: string) {
  const parts = content.split(/(```[\s\S]*?```|`[^`]+`|\*\*[^*]+\*\*)/g);

  return parts.map((part, i) => {
    if (part.startsWith("```") && part.endsWith("```")) {
      const code = part.slice(3, -3).replace(/^\w+\n/, "");
      return (
        <pre key={i}>
          <code>{code}</code>
        </pre>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`animate-fade-in py-6 ${isUser ? "" : "bg-[var(--bg-secondary)]/50"}`}>
      <div className="mx-auto max-w-3xl px-4">
        <div className="flex gap-4">
          <div
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-medium ${
              isUser ? "bg-blue-600 text-white" : "bg-green-600 text-white"
            }`}
          >
            {isUser ? "You" : "AI"}
          </div>
          <div className="min-w-0 flex-1">
            <div className="markdown-content text-[15px] leading-relaxed text-[var(--text-primary)]">
              {formatContent(message.content)}
            </div>
            {!isUser && (
              <div className="mt-3 flex items-center gap-1">
                <button className="rounded-lg p-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]">
                  <Copy size={14} />
                </button>
                <button className="rounded-lg p-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]">
                  <ThumbsUp size={14} />
                </button>
                <button className="rounded-lg p-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]">
                  <ThumbsDown size={14} />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="animate-fade-in py-6">
      <div className="mx-auto max-w-3xl px-4">
        <div className="flex gap-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-600 text-xs font-medium text-white">
            AI
          </div>
          <div className="flex items-center gap-1 pt-2">
            <div className="typing-dot h-2 w-2 rounded-full bg-[var(--text-secondary)]" />
            <div className="typing-dot h-2 w-2 rounded-full bg-[var(--text-secondary)]" />
            <div className="typing-dot h-2 w-2 rounded-full bg-[var(--text-secondary)]" />
          </div>
        </div>
      </div>
    </div>
  );
}

interface ChatInputProps {
  onSend: (message: string, fileIds: string[]) => void;
  onUpload: (file: File) => Promise<UploadedFile>;
  disabled?: boolean;
  isAuthenticated: boolean;
  onLoginRequired: () => void;
}

export function ChatInput({
  onSend,
  onUpload,
  disabled,
  isAuthenticated,
  onLoginRequired,
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (!input.trim() && attachedFiles.length === 0) return;

    if (!isAuthenticated) {
      onLoginRequired();
      return;
    }

    onSend(
      input.trim(),
      attachedFiles.map((f) => f.id)
    );
    setInput("");
    setAttachedFiles([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!isAuthenticated) {
      onLoginRequired();
      return;
    }

    setUploading(true);
    try {
      const uploaded = await onUpload(file);
      setAttachedFiles((prev) => [...prev, uploaded]);
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeFile = (id: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-6">
      {attachedFiles.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {attachedFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center gap-2 rounded-lg bg-[var(--bg-tertiary)] px-3 py-1.5 text-sm"
            >
              <Paperclip size={14} className="text-[var(--text-secondary)]" />
              <span className="max-w-[200px] truncate">{file.original_name}</span>
              <button onClick={() => removeFile(file.id)} className="text-[var(--text-secondary)] hover:text-white">
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="relative flex items-end rounded-3xl border border-[var(--border-color)] bg-[var(--bg-secondary)] shadow-lg transition-colors focus-within:border-white/20">
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          accept=".txt,.md,.pdf,.csv,.json,.py,.js,.ts,.tsx,.jsx,.html,.css,.xml,.yaml,.yml,.doc,.docx"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="flex shrink-0 items-center justify-center p-3 text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)] disabled:opacity-50"
          title="Attach file"
        >
          <Paperclip size={20} />
        </button>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            e.target.style.height = "auto";
            e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
          }}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything"
          rows={1}
          disabled={disabled}
          className="max-h-[200px] min-h-[24px] flex-1 resize-none bg-transparent py-3 pr-2 text-[15px] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none"
        />

        <button
          onClick={handleSubmit}
          disabled={disabled || (!input.trim() && attachedFiles.length === 0)}
          className="m-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white text-black transition-opacity hover:opacity-90 disabled:opacity-30"
        >
          <Send size={16} />
        </button>
      </div>

      <p className="mt-2 text-center text-xs text-[var(--text-secondary)]">
        ChatGPT is AI and can make mistakes. Check important info.
      </p>
    </div>
  );
}
