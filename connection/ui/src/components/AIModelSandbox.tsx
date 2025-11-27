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
  
  const normalizedModel =
  selectedModel === "baseline-llava" ? "llava" :
  selectedModel === "qwen-2.5-xb" ? "qwen" :
  selectedModel;

  const blobFromImageSource = async (imageSource: string) => {
    const response = await fetch(imageSource);
    if (!response.ok) {
      throw new Error("Unable to read selected image.");
    }
    return response.blob();
  };

  const handleSendMessage = async (content: string, image?: string) => {
    if (!currentSessionId) return;
  
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
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
      const userId = currentSessionId || "default";
      // ✅ Call your FastAPI /generate_cad endpoint
      // Use Modal backend URL if provided, otherwise fall back to localhost or proxy
      const modalBackendUrl = import.meta.env.VITE_MODAL_BACKEND_URL || "";
      const useProxy = import.meta.env.DEV && import.meta.env.VITE_USE_PROXY !== 'false' && !modalBackendUrl;
      
      const baseUrl = modalBackendUrl || (useProxy ? "" : "http://localhost:8000");
      const backendUrl = `${baseUrl}/generate_cad`;
      const uploadUrl = `${baseUrl}/upload/`;

      let uploadArtifacts: any = null;
      if (image) {
        console.log("Uploading image via:", uploadUrl);
        const blob = await blobFromImageSource(image);
        const extension = blob.type.split("/")[1] || "png";
        const formData = new FormData();
        formData.append("file", blob, `upload-${Date.now()}.${extension}`);
        formData.append("user_id", userId);
        formData.append("prompt", content);

        const uploadResponse = await fetch(uploadUrl, {
          method: "POST",
          body: formData
        });

        if (!uploadResponse.ok) {
          let errorMessage = `Upload failed with status ${uploadResponse.status}`;
          try {
            const uploadError = await uploadResponse.json();
            errorMessage = uploadError.detail || JSON.stringify(uploadError);
          } catch (uploadParseError) {
            console.error("Unable to parse upload error:", uploadParseError);
          }
          throw new Error(errorMessage);
        }

        uploadArtifacts = await uploadResponse.json();
        console.log("Upload response:", uploadArtifacts);
      }

      const cachedImagePath =
        uploadArtifacts?.preprocess?.artifacts?.image_path ??
        (image && !image.startsWith("data:") ? image : null);
      console.log("Making request to:", backendUrl, "(proxy:", useProxy, ")");
      console.log("Request payload:", {
        prompt: content,
        image_path: cachedImagePath || image || null,
        user_id: userId,
        model_choice: normalizedModel,
        rag_context: null
      });

      const response = await fetch(backendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: content,
          image_path: cachedImagePath || image || null,
          user_id: userId,
          model_choice: normalizedModel,  // must be "llava" or "qwen"
          rag_context: null
        }),
      });
  
      console.log("Response status:", response.status, response.statusText);
      console.log("Response headers:", Object.fromEntries(response.headers.entries()));
  
      // Check if response is OK before parsing
      if (!response.ok) {
        let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorData.message || errorDetail;
          console.error("Backend error response:", errorData);
        } catch (e) {
          // If we can't parse error JSON, use status text
          try {
            const errorText = await response.text();
            if (errorText) errorDetail = errorText.substring(0, 200);
          } catch (textError) {
            console.error("Could not read error response:", textError);
          }
        }
        throw new Error(errorDetail);
      }
  
      // Parse the backend response
      const data = await response.json();
      console.log("Backend raw response:", data);
  
      // ✅ Safely extract CAD code from response
      const backendOutput =
        data.cad_code ||
        data.generated_code ||
        data.output ||
        data.result ||
        "⚙️ Backend responded but no CAD code field found.";
  
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: backendOutput,
        timestamp: new Date(),
        model: getModelName(selectedModel),
      };
  
      // Add assistant reply to the current chat session
      setSessions(prev =>
        prev.map(session =>
          session.id === currentSessionId
            ? { ...session, messages: [...session.messages, assistantMessage] }
            : session
        )
      );
    } catch (error) {
      console.error("Error contacting backend:", error);
      console.error("Error type:", error instanceof TypeError ? "Network/CORS error" : "HTTP/Application error");
      console.error("Error details:", {
        name: error instanceof Error ? error.name : "Unknown",
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined
      });

      let errorMessage: string;
      if (error instanceof TypeError && error.message.includes("fetch")) {
        // Network error (CORS, connection refused, etc.)
        errorMessage = `Network error: Unable to connect to backend at http://localhost:8000. This could be due to:\n- Backend not running\n- CORS configuration issue\n- Firewall blocking the connection\n\nPlease check the browser console for more details.`;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      } else {
        errorMessage = String(error);
      }

      const userFriendlyError: Message = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content: `❌ ${errorMessage}`,
        timestamp: new Date(),
        model: getModelName(selectedModel),
      };
      setSessions(prev =>
        prev.map(session =>
          session.id === currentSessionId
            ? { ...session, messages: [...session.messages, userFriendlyError] }
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