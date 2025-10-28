import { useState } from "react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Separator } from "./ui/separator";
import { Card } from "./ui/card";
import { Plus, MessageSquare, Trash2 } from "lucide-react";
import { Message } from "./ChatMessage";

interface ChatSession {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
  model: string;
}

interface ChatSidebarProps {
  currentSessionId: string | null;
  sessions: ChatSession[];
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
}

export function ChatSidebar({ 
  currentSessionId, 
  sessions, 
  onSessionSelect, 
  onNewSession, 
  onDeleteSession 
}: ChatSidebarProps) {
  const [hoveredSession, setHoveredSession] = useState<string | null>(null);

  const formatSessionName = (session: ChatSession) => {
    if (session.messages.length === 0) {
      return "New Chat";
    }
    const firstMessage = session.messages.find(m => m.role === "user");
    if (firstMessage) {
      return firstMessage.content.slice(0, 30) + (firstMessage.content.length > 30 ? "..." : "");
    }
    return "New Chat";
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
      return "Today";
    } else if (diffDays === 2) {
      return "Yesterday";
    } else if (diffDays <= 7) {
      return `${diffDays - 1} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="w-80 bg-sidebar border-r border-sidebar-border flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border">
        <Button
          onClick={onNewSession}
          className="w-full bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary/90"
        >
          <Plus className="size-4 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Chat Sessions */}
      <ScrollArea className="flex-1 p-2">
        <div className="space-y-2">
          {sessions.length === 0 ? (
            <div className="text-center py-8 text-sidebar-foreground/60">
              <MessageSquare className="size-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No chat sessions yet</p>
              <p className="text-xs text-sidebar-foreground/40">Start a new conversation</p>
            </div>
          ) : (
            sessions.map((session) => (
              <Card
                key={session.id}
                className={`p-3 cursor-pointer transition-colors border-sidebar-border bg-sidebar hover:bg-sidebar-accent group ${
                  currentSessionId === session.id 
                    ? "bg-sidebar-accent border-sidebar-primary" 
                    : ""
                }`}
                onClick={() => onSessionSelect(session.id)}
                onMouseEnter={() => setHoveredSession(session.id)}
                onMouseLeave={() => setHoveredSession(null)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm text-sidebar-foreground truncate">
                      {formatSessionName(session)}
                    </h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-sidebar-foreground/60">
                        {session.model}
                      </span>
                      <span className="text-xs text-sidebar-foreground/40">•</span>
                      <span className="text-xs text-sidebar-foreground/60">
                        {formatDate(session.createdAt)}
                      </span>
                    </div>
                    <p className="text-xs text-sidebar-foreground/50 mt-1">
                      {session.messages.length} messages
                    </p>
                  </div>
                  
                  {hoveredSession === session.id && sessions.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(session.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 h-auto text-sidebar-foreground/60 hover:text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="size-3" />
                    </Button>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-4 border-t border-sidebar-border">
        <div className="text-xs text-sidebar-foreground/60 text-center">
          CAD-Coder Sandbox
        </div>
      </div>
    </div>
  );
}

export type { ChatSession };