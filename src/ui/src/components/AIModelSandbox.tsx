import { useState, useEffect } from "react";
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
  "qwen3-vl-2b": [
    "Hello! I'm Qwen3-VL-2B-Instruct, a vision-language model fine-tuned for CAD code generation. What would you like to work on?",
    "I'm Qwen3-VL-2B-Instruct, designed for complex problem-solving and CAD code generation tasks. How can I help you today?",
    "Hi! I'm Qwen3-VL-2B-Instruct, ready to assist with CAD code generation and technical challenges."
  ]
};

// Multimodal responses for when images are provided
const MULTIMODAL_RESPONSES: Record<string, string[]> = {
  "baseline-llava": [
    "I can see the image you've shared. As Baseline-LLaVA, I'm specifically designed to understand and analyze visual content alongside text.",
    "Thanks for the image! I can examine visual details and provide comprehensive analysis of what I observe in the image.",
    "I'm analyzing the visual content you've provided. My vision-language capabilities allow me to understand both the visual elements and their context."
  ],
  "qwen3-vl-2b": [
    "I can see the image you've uploaded. As Qwen3-VL-2B-Instruct, I can analyze visual content and generate CAD code based on what I see.",
    "Thanks for sharing the image! I can process visual information and generate CadQuery code to recreate the CAD model shown.",
    "I'm examining the image you've provided. Let me analyze the visual elements and generate the appropriate CAD code."
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
      "qwen3-vl-2b": "Qwen3-VL-2B-Instruct"
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

  // Update current session's model when model selection changes
  useEffect(() => {
    if (currentSessionId) {
      setSessions(prev => prev.map(session => 
        session.id === currentSessionId 
          ? { ...session, model: getModelName(selectedModel) }
          : session
      ));
    }
  }, [selectedModel, currentSessionId]);

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
  
  const normalizedModel =
  selectedModel === "baseline-llava" ? "llava" :
  selectedModel === "qwen3-vl-2b" ? "qwen" :
  selectedModel;

  const handleSendMessage = async (content: string, image?: string) => {
    if (!currentSessionId) return;
  
    // Ensure we have either content or image
    const messageContent = content.trim() || (image ? "Generate CAD code for this image" : "");
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageContent,
      timestamp: new Date(),
      image,
    };
  
    // Add the user message to the session
    setSessions(prev =>
      prev.map(session =>
        session.id === currentSessionId
          ? { ...session, messages: [...session.messages, userMessage] }
          : session
      )
    );
  
    setIsGenerating(true);
  
    try {
      // ✅ Call your FastAPI /generate_cad endpoint
      const requestBody = {
        prompt: messageContent,
        image_path: image || null,
        user_id: "default",
        model_choice: normalizedModel,  // must be "llava" or "qwen"
        rag_context: null
      };
      
      console.log("[Frontend] Selected model:", selectedModel);
      console.log("[Frontend] Normalized model:", normalizedModel);
      console.log("[Frontend] Request body:", requestBody);
      
      // Use relative URL to work with the ingress routing in production
      // In production, /api/* routes to the backend service
      const apiUrl = import.meta.env.VITE_API_URL || "/api";

      // Prepare streaming response
      const response = await fetch(`${apiUrl}/generate_cad_stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Seed assistant message
      const assistantId = (Date.now() + 1).toString();
      setSessions(prev =>
        prev.map(session =>
          session.id === currentSessionId
            ? {
                ...session,
                messages: [
                  ...session.messages,
                  {
                    id: assistantId,
                    role: "assistant",
                    content: "",
                    timestamp: new Date(),
                    model: getModelName(selectedModel),
                  },
                ],
              }
            : session
        )
      );

      // Read and append chunks
      let accumulated = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        accumulated += chunk;

        setSessions(prev =>
          prev.map(session =>
            session.id === currentSessionId
              ? {
                  ...session,
                  messages: session.messages.map(msg =>
                    msg.id === assistantId
                      ? { ...msg, content: accumulated }
                      : msg
                  ),
                }
              : session
          )
        );
      }
    } catch (error) {
      console.error("Error contacting backend:", error);
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content:
          "❌ Failed to reach backend or received an invalid response. Please try again.",
        timestamp: new Date(),
        model: getModelName(selectedModel),
      };
      setSessions(prev =>
        prev.map(session =>
          session.id === currentSessionId
            ? { ...session, messages: [...session.messages, errorMessage] }
            : session
        )
      );
    } finally {
      setIsGenerating(false);
    }
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