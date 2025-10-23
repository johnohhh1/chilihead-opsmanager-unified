"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface OperationsChatProps {
  dailyDigest?: string;
  operations?: any[];
}

interface ModelOption {
  id: string;
  name: string;
  provider: string;
  default?: boolean;
}

export default function OperationsChat({ dailyDigest, operations }: OperationsChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("gpt-4o");
  const [availableModels, setAvailableModels] = useState<ModelOption[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<string>("unknown");
  const [modelsLoading, setModelsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load available models when component mounts
  useEffect(() => {
    loadModels();
  }, []);

  // Load chat history from PostgreSQL when opening
  useEffect(() => {
    if (isOpen && !sessionId) {
      loadRecentSession();
    }
  }, [isOpen]);

  // Load available AI models
  const loadModels = async () => {
    setModelsLoading(true);
    try {
      const response = await fetch('/api/backend/models/list', {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.models || []);
        setOllamaStatus(data.ollama_status || "unknown");

        // Load saved model preference from localStorage
        const savedModel = localStorage.getItem('preferred-ai-model');
        if (savedModel) {
          setSelectedModel(savedModel);
        }
      }
    } catch (error) {
      console.error('Failed to load models:', error);
      setOllamaStatus("error");
    } finally {
      setModelsLoading(false);
    }
  };

  // Handle model selection change
  const handleModelChange = (modelId: string) => {
    setSelectedModel(modelId);
    localStorage.setItem('preferred-ai-model', modelId);
  };

  // Load most recent chat session from database
  const loadRecentSession = async () => {
    try {
      const response = await fetch('/api/operations-chat/sessions');
      if (response.ok) {
        const data = await response.json();
        if (data.sessions && data.sessions.length > 0) {
          const recentSession = data.sessions[0];
          setSessionId(recentSession.id);

          // Load messages for this session
          const historyResponse = await fetch(`/api/operations-chat/history/${recentSession.id}`);
          if (historyResponse.ok) {
            const historyData = await historyResponse.json();
            const loadedMessages = historyData.messages.map((msg: any) => ({
              role: msg.role,
              content: msg.content,
              timestamp: new Date(msg.timestamp)
            }));
            setMessages(loadedMessages);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
      // If no history, show welcome message
      if (dailyDigest && messages.length === 0) {
        setMessages([
          {
            role: "assistant",
            content: `Hi John! I've analyzed your operations for today. What would you like to know?`,
            timestamp: new Date()
          }
        ]);
      }
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/operations-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
          model: selectedModel,  // Include selected model
          context: {
            dailyDigest,
            operations
          }
        })
      });

      if (!response.ok) throw new Error("Failed to get response");

      const data = await response.json();

      // Update session ID if it's a new session
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, I had trouble processing that. Please try again.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-red-600 hover:bg-red-700 text-white rounded-full p-4 shadow-lg transition-all z-50"
        title="Chat about operations"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-gray-800 rounded-lg shadow-2xl flex flex-col z-50 border border-gray-700">
      {/* Header */}
      <div className="bg-red-600 text-white p-4 rounded-t-lg flex justify-between items-center">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <h3 className="font-semibold">Operations Assistant</h3>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="hover:bg-red-700 rounded p-1 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Model Selector */}
      <div className="bg-gray-800 border-b border-gray-700 p-3">
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs text-gray-400">AI Model:</label>
          <button
            onClick={loadModels}
            disabled={modelsLoading}
            className="text-xs text-gray-400 hover:text-white transition-colors disabled:opacity-50"
            title="Refresh model list"
          >
            <svg
              className={`w-3 h-3 ${modelsLoading ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        <select
          value={selectedModel}
          onChange={(e) => handleModelChange(e.target.value)}
          className="w-full bg-gray-700 text-white text-sm px-3 py-2 rounded border border-gray-600 focus:ring-2 focus:ring-red-500 focus:border-red-500"
          disabled={modelsLoading}
        >
          {availableModels.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
        {ollamaStatus === "disconnected" && (
          <p className="text-xs text-yellow-400 mt-1">⚠ Ollama offline - run: ollama serve</p>
        )}
        {ollamaStatus === "connected" && availableModels.filter(m => m.provider === "ollama").length > 0 && (
          <p className="text-xs text-green-400 mt-1">✓ Ollama connected</p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-900">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-8">
            <p className="text-sm">Ask me anything about your daily operations!</p>
            <p className="text-xs mt-2">Try: "What's urgent today?" or "Show me my deadlines"</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === "user"
                  ? "bg-red-600 text-white"
                  : "bg-gray-700 text-gray-100 border border-gray-600"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              <p className={`text-xs mt-1 ${msg.role === "user" ? "text-red-100" : "text-gray-400"}`}>
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg p-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-700 bg-gray-800 rounded-b-lg">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your operations..."
            className="flex-1 border border-gray-600 bg-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 placeholder-gray-400"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">Press Enter to send, Shift+Enter for new line</p>
      </div>
    </div>
  );
}
