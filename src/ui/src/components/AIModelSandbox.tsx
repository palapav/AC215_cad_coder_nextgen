import { useState } from "react";
import { ModelSelector } from "./ModelSelector";
import { ChatHistory } from "./ChatHistory";
import { ChatInput } from "./ChatInput";
import { Message } from "./ChatMessage";
import { ChatSidebar, ChatSession } from "./ChatSidebar";
import { Button } from "./ui/button";
import { Trash2, Settings } from "lucide-react";

// Mock AI responses for different models
const MODEL_RESPONSES: Record<string, string[]> = {
  "baseline-llava": [
    "Hello! I'm Baseline-LLaVA, a vision-language model. I can help with both text and image analysis tasks.",
    "I'm Baseline-LLaVA, designed to understand both visual and textual content. How can I assist you today?",
    "Hi! I'm Baseline-LLaVA, ready to help with multimodal tasks involving text and images."
  ],
  "qwen-2.5-xb": [
    "Hello! I'm Qwen-2.5-xB, specializing in advanced reasoning and code generation. What would you like to work on?",
    "I'm Qwen-2.5-xB, designed for complex problem-solving and coding tasks. How can I help you today?",
    "Hi! I'm Qwen-2.5-xB, ready to assist with sophisticated reasoning and development challenges."
  ]
};

// Multimodal responses for when images are provided
const MULTIMODAL_RESPONSES: Record<string, string[]> = {
  "baseline-llava": [
    "I can see the image you've shared. As Baseline-LLaVA, I'm specifically designed to understand and analyze visual content alongside text.",
    "Thanks for the image! I can examine visual details and provide comprehensive analysis of what I observe in the image.",
    "I'm analyzing the visual content you've provided. My vision-language capabilities allow me to understand both the visual elements and their context."
  ],
  "qwen-2.5-xb": [
    "I can see the image you've uploaded. As Qwen-2.5-xB, I can analyze visual content and provide detailed technical insights.",
    "Thanks for sharing the image! I can process visual information and provide thorough analysis, especially for technical or code-related content.",
    "I'm examining the image you've provided. Let me analyze the visual elements and provide comprehensive feedback."
  ]
};

export function AIModelSandbox() {
  const [selectedModel, setSelectedModel] = useState("baseline-llava");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  // Get current session messages
  const currentSession = sessions.find(s => s.id === currentSessionId);
  const messages = currentSession?.messages || [];
  
  const getModelName = (modelId: string) => {
    const modelNames: Record<string, string> = {
      "baseline-llava": "Baseline-LLaVA",
      "qwen-2.5-xb": "Qwen-2.5-xB"
    };
    return modelNames[modelId] || modelId;
  };
  
  const generateMockResponse = (userMessage: string, modelId: string, hasImage: boolean): string => {
    // Use multimodal responses if image is provided
    const responsesPool = hasImage ? MULTIMODAL_RESPONSES[modelId] : MODEL_RESPONSES[modelId];
    const responses = responsesPool || MODEL_RESPONSES["baseline-llava"];
    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
    
    // Simple logic to make responses feel more contextual
    if (userMessage.toLowerCase().includes("hello") || userMessage.toLowerCase().includes("hi")) {
      return randomResponse;
    }
    
    if (hasImage) {
      return randomResponse;
    }
    
    return `Thanks for your question about "${userMessage.slice(0, 50)}${userMessage.length > 50 ? "..." : ""}". ${randomResponse.split(". ").slice(1).join(". ")}`;
  };

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      name: "New Chat",
      messages: [],
      createdAt: new Date(),
      model: getModelName(selectedModel)
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  };

  const deleteSession = (sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      const remainingSessions = sessions.filter(s => s.id !== sessionId);
      if (remainingSessions.length > 0) {
        setCurrentSessionId(remainingSessions[0].id);
      } else {
        setCurrentSessionId(null);
      }
    }
  };

  const selectSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
  };

  // Create initial session if none exists
  if (sessions.length === 0 && !currentSessionId) {
    const initialSession: ChatSession = {
      id: "initial",
      name: "New Chat",
      messages: [],
      createdAt: new Date(),
      model: getModelName(selectedModel)
    };
    setSessions([initialSession]);
    setCurrentSessionId(initialSession.id);
  }
  
  const handleSendMessage = async (content: string, image?: string) => {
    if (!currentSessionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
      image
    };
    
    // Update current session with new message
    setSessions(prev => prev.map(session => 
      session.id === currentSessionId 
        ? { ...session, messages: [...session.messages, userMessage] }
        : session
    ));
    
    setIsGenerating(true);
    
    // Simulate AI response delay
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: generateMockResponse(content, selectedModel, !!image),
        timestamp: new Date(),
        model: getModelName(selectedModel)
      };
      
      setSessions(prev => prev.map(session => 
        session.id === currentSessionId 
          ? { ...session, messages: [...session.messages, assistantMessage] }
          : session
      ));
      setIsGenerating(false);
    }, 1000 + Math.random() * 2000); // Random delay between 1-3 seconds
  };
  
  const clearChat = () => {
    if (!currentSessionId) return;
    
    setSessions(prev => prev.map(session => 
      session.id === currentSessionId 
        ? { ...session, messages: [] }
        : session
    ));
  };
  
  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <ChatSidebar
        currentSessionId={currentSessionId}
        sessions={sessions}
        onSessionSelect={selectSession}
        onNewSession={createNewSession}
        onDeleteSession={deleteSession}
      />
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1>CAD-Coder Sandbox</h1>
              <ModelSelector 
                selectedModel={selectedModel} 
                onModelChange={setSelectedModel} 
              />
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={clearChat}
                disabled={messages.length === 0}
              >
                <Trash2 className="size-4 mr-2" />
                Clear Chat
              </Button>
              <Button variant="outline" size="sm">
                <Settings className="size-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>
        
        {/* Chat Area */}
        <ChatHistory messages={messages} />
        
        {/* Input Area */}
        <ChatInput onSendMessage={handleSendMessage} disabled={isGenerating} />
        
        {isGenerating && (
          <div className="text-center text-muted-foreground py-2">
            <span className="inline-flex items-center gap-1">
              <div className="animate-spin size-4 rounded-full border-2 border-muted-foreground border-t-transparent"></div>
              {getModelName(selectedModel)} is thinking...
            </span>
          </div>
        )}
      </div>
    </div>
  );
}