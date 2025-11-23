import { useState, useRef } from "react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Send, Paperclip, X } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
/*import { generateCADCode } from "../hooks/useApi";*/

interface ChatInputProps {
  onSendMessage: (message: string, image?: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((message.trim() || selectedImage) && !disabled) {
      // Just send the message to the parent component
      onSendMessage(message.trim(), selectedImage || undefined);
  
      // Reset input + image
      setMessage("");
      setSelectedImage(null);
    }
  };
   

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="border-t border-border bg-background p-4">
      <div className="max-w-4xl mx-auto">
        {selectedImage && (
          <div className="mb-3 p-3 bg-muted rounded-lg">
            <div className="flex items-start gap-3">
              <ImageWithFallback
                src={selectedImage}
                alt="Selected image"
                className="w-20 h-20 object-cover rounded-lg"
              />
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">Image attached</p>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={removeImage}
                  className="mt-1 h-auto p-1 text-muted-foreground hover:text-foreground"
                >
                  <X className="size-4" />
                  Remove
                </Button>
              </div>
            </div>
          </div>
        )}
        
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              className="min-h-[50px] max-h-[200px] resize-none bg-input-background border-border pr-12"
              disabled={disabled}
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              className="absolute bottom-2 right-2 p-2 h-auto"
              disabled={disabled}
            >
              <Paperclip className="size-4" />
              <span className="sr-only">Attach image</span>
            </Button>
          </div>
          
          <Button 
            type="submit" 
            disabled={(!message.trim() && !selectedImage) || disabled}
            className="px-3"
          >
            <Send className="size-4" />
            <span className="sr-only">Send message</span>
          </Button>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageSelect}
          className="hidden"
        />
      </div>
    </form>
  );
}