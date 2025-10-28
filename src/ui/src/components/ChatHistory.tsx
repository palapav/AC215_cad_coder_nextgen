import { useEffect, useRef } from "react";
import { ScrollArea } from "./ui/scroll-area";
import { ChatMessage, Message } from "./ChatMessage";

interface ChatHistoryProps {
  messages: Message[];
}

export function ChatHistory({ messages }: ChatHistoryProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <h3 className="mb-2">Welcome to CAD-Coder AI Model Sandbox</h3>
          <p>Select a model and start chatting to test AI capabilities in CAD code generation.</p>
        </div>
      </div>
    );
  }
  
  return (
    <ScrollArea className="flex-1">
      <div className="max-w-4xl mx-auto">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}