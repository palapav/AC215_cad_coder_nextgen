import { Avatar, AvatarFallback } from "./ui/avatar";
import { Card } from "./ui/card";
import { Bot, User } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  model?: string;
  image?: string; // Base64 or URL for uploaded images
}

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  
  return (
    <div className={`flex gap-4 p-4 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <Avatar className="size-8">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <Bot className="size-4" />
          </AvatarFallback>
        </Avatar>
      )}
      
      <Card className={`max-w-[80%] p-4 ${
        isUser 
          ? "bg-primary text-primary-foreground ml-auto" 
          : "bg-muted"
      }`}>
        {message.image && (
          <div className="mb-3">
            <ImageWithFallback
              src={message.image}
              alt="Uploaded image"
              className="max-w-full h-auto rounded-lg max-h-96 object-contain"
            />
          </div>
        )}
        <div className="whitespace-pre-wrap">{message.content}</div>
        {message.model && !isUser && (
          <div className="text-xs text-muted-foreground mt-2">
            {message.model}
          </div>
        )}
      </Card>
      
      {isUser && (
        <Avatar className="size-8">
          <AvatarFallback className="bg-secondary text-secondary-foreground">
            <User className="size-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}