"use client";

import {
  HelpCircle,
  Image,
  LogOut,
  MessageSquarePlus,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings,
  Sparkles,
} from "lucide-react";
import clsx from "clsx";

import type { Conversation } from "@/lib/api";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  collapsed: boolean;
  userName: string | null;
  userEmail: string | null;
  onToggle: () => void;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onLogin: () => void;
  onLogout: () => void;
  isAuthenticated: boolean;
}

export function Sidebar({
  conversations,
  activeId,
  collapsed,
  userName,
  userEmail,
  onToggle,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  onLogin,
  onLogout,
  isAuthenticated,
}: SidebarProps) {
  const initials = userName
    ? userName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "?";

  if (collapsed) {
    return (
      <div className="flex h-full w-[52px] flex-col items-center border-r border-[var(--border-color)] bg-[var(--bg-secondary)] py-3">
        <button
          onClick={onToggle}
          className="mb-4 rounded-lg p-2 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
          title="Open sidebar"
        >
          <PanelLeftOpen size={20} />
        </button>
        <button
          onClick={onNewChat}
          className="rounded-lg p-2 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
          title="New chat"
        >
          <MessageSquarePlus size={20} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-full w-[260px] flex-col border-r border-[var(--border-color)] bg-[var(--bg-secondary)]">
      <div className="flex items-center justify-between p-3">
        <button
          onClick={onNewChat}
          className="flex flex-1 items-center gap-2 rounded-lg border border-[var(--border-color)] px-3 py-2 text-sm text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-hover)]"
        >
          <MessageSquarePlus size={16} />
          New chat
        </button>
        <button
          onClick={onToggle}
          className="ml-2 rounded-lg p-2 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
          title="Close sidebar"
        >
          <PanelLeftClose size={18} />
        </button>
      </div>

      <nav className="px-2">
        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]">
          <Search size={16} />
          Search chats
        </button>
        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]">
          <Image size={16} />
          Images
        </button>
        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]">
          <Sparkles size={16} />
          Apps
        </button>
      </nav>

      <div className="mt-4 flex-1 overflow-y-auto px-2">
        {conversations.length > 0 && (
          <div>
            <p className="px-3 py-1 text-xs font-medium text-[var(--text-secondary)]">Recents</p>
            <div className="mt-1 space-y-0.5">
              {conversations.map((conv) => (
                <div key={conv.id} className="group relative">
                  <button
                    onClick={() => onSelectConversation(conv.id)}
                    className={clsx(
                      "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors",
                      activeId === conv.id
                        ? "bg-[var(--bg-hover)] text-[var(--text-primary)]"
                        : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                    )}
                  >
                    <span className="truncate">{conv.title}</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    className="absolute right-2 top-1/2 hidden -translate-y-1/2 rounded px-1.5 py-0.5 text-xs text-red-400 group-hover:block hover:bg-[var(--bg-tertiary)]"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-[var(--border-color)] p-2">
        {isAuthenticated ? (
          <div className="space-y-1">
            <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]">
              <Settings size={16} />
              Settings
            </button>
            <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]">
              <HelpCircle size={16} />
              Help
            </button>
            <button
              onClick={onLogout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
            >
              <LogOut size={16} />
              Log out
            </button>
            <div className="mt-2 flex items-center gap-3 rounded-lg px-3 py-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-medium text-white">
                {initials}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{userName}</p>
                <p className="truncate text-xs text-[var(--text-secondary)]">{userEmail}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-2 p-2">
            <p className="text-xs text-[var(--text-secondary)]">
              Get responses tailored to you
            </p>
            <button
              onClick={onLogin}
              className="w-full rounded-full bg-[var(--bg-hover)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-tertiary)]"
            >
              Log in
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
