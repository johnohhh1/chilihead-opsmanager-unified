"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { X, MessageSquare, Sparkles, Maximize2, Minimize2 } from 'lucide-react';

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface DailyBriefModalProps {
  digest: string;
  generatedAt?: string;
  sessionId?: string;
  onClose: () => void;
}

export default function DailyBriefModal({ digest, generatedAt, sessionId: initialSessionId, onClose }: DailyBriefModalProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId || null);
  const [selectedModel, setSelectedModel] = useState<string>("gpt-4o");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [leftPanelWidth, setLeftPanelWidth] = useState(50); // percentage
  const [isDragging, setIsDragging] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initialize with welcome message from AUBS
  useEffect(() => {
    setMessages([
      {
        role: "assistant",
        content: "Hey John! I just wrote this morning's brief for you. Ask me anything about it - what's urgent, what can wait, who you need to follow up with. Let's knock out today's priorities.",
        timestamp: new Date()
      }
    ]);
  }, []);

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
          model: selectedModel,
          context: {
            dailyDigest: digest,
            operations: []
          }
        })
      });

      if (!response.ok) throw new Error("Failed to get response");

      const data = await response.json();

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

  // Handle dragging the divider
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const container = containerRef.current;
      const containerRect = container.getBoundingClientRect();
      const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;

      // Constrain between 30% and 70%
      if (newWidth >= 30 && newWidth <= 70) {
        setLeftPanelWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className={`bg-gray-800 rounded-lg shadow-2xl ${isFullscreen ? 'w-full h-full' : 'max-w-7xl w-full h-[90vh]'} flex flex-col border border-gray-700 transition-all duration-200`}>

        {/* Header */}
        <div className="bg-gradient-to-r from-blue-700 to-blue-600 text-white p-6 rounded-t-lg flex justify-between items-center border-b border-blue-500">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="h-6 w-6" />
              Your Daily Operations Brief
            </h2>
            <p className="text-blue-100 text-sm mt-1">
              {generatedAt ? `Generated ${new Date(generatedAt).toLocaleTimeString()}` : 'Morning brief'} — Chat with AUBS about your priorities
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="hover:bg-blue-600 rounded-lg p-2 transition-colors"
              title={isFullscreen ? "Restore size" : "Maximize"}
            >
              {isFullscreen ? <Minimize2 className="h-5 w-5" /> : <Maximize2 className="h-5 w-5" />}
            </button>
            <button
              onClick={onClose}
              className="hover:bg-blue-600 rounded-lg p-2 transition-colors"
              title="Close"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Split Panel Layout */}
        <div className="flex-1 flex overflow-hidden" ref={containerRef}>

          {/* Left Panel - Brief Content */}
          <div
            className="overflow-y-auto p-8 bg-gray-900"
            style={{ width: `${leftPanelWidth}%` }}
          >
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => <h1 className="text-3xl font-bold text-white mb-5 tracking-wide">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-2xl font-bold text-white mt-8 mb-4 tracking-wide">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-xl font-semibold text-white mt-6 mb-3 tracking-wide">{children}</h3>,
                  h4: ({ children }) => <h4 className="text-lg font-semibold text-white mt-4 mb-2">{children}</h4>,
                  p: ({ children }) => <p className="text-white mb-4 leading-loose text-base">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc list-outside ml-6 text-white space-y-2 mb-5">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-outside ml-6 text-white space-y-2 mb-5">{children}</ol>,
                  li: ({ children }) => <li className="text-white leading-relaxed">{children}</li>,
                  strong: ({ children }) => <strong className="text-yellow-300 font-bold">{children}</strong>,
                  code: ({ children }) => <code className="bg-gray-800 text-emerald-400 px-2 py-1 rounded text-sm font-mono">{children}</code>,
                  a: ({ href, children }) => <a href={href} className="text-blue-400 hover:text-blue-300 underline font-medium">{children}</a>,
                  em: ({ children }) => <em className="text-gray-300 italic">{children}</em>,
                  table: ({ children }) => <table className="w-full border-collapse border border-gray-600 my-4 text-white">{children}</table>,
                  thead: ({ children }) => <thead className="bg-gray-700">{children}</thead>,
                  tbody: ({ children }) => <tbody>{children}</tbody>,
                  tr: ({ children }) => <tr className="border-b border-gray-600">{children}</tr>,
                  th: ({ children }) => <th className="border border-gray-600 px-4 py-2 text-left font-bold text-white">{children}</th>,
                  td: ({ children }) => <td className="border border-gray-600 px-4 py-2 text-white">{children}</td>,
                }}
              >
                {digest || "No digest available"}
              </ReactMarkdown>
            </div>
          </div>

          {/* Draggable Divider */}
          <div
            className={`w-1 bg-gray-700 hover:bg-blue-500 cursor-col-resize transition-colors ${isDragging ? 'bg-blue-500' : ''}`}
            onMouseDown={handleMouseDown}
          />

          {/* Right Panel - Chat with AUBS */}
          <div
            className="flex flex-col bg-gray-800"
            style={{ width: `${100 - leftPanelWidth}%` }}
          >

            {/* Chat Header */}
            <div className="bg-gray-700 p-4 border-b border-gray-600">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-red-400" />
                <h3 className="font-semibold text-white">Chat with AUBS about this brief</h3>
              </div>
              <p className="text-xs text-gray-400 mt-1">Ask about priorities, deadlines, or what to tackle first</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
                    {msg.role === "user" ? (
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="text-sm prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({ children }) => <p className="text-gray-100 mb-2">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc list-inside text-gray-100 space-y-1 mb-2">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside text-gray-100 space-y-1 mb-2">{children}</ol>,
                            li: ({ children }) => <li className="text-gray-100">{children}</li>,
                            strong: ({ children }) => <strong className="text-white font-bold">{children}</strong>,
                            code: ({ children }) => <code className="bg-gray-800 text-emerald-400 px-1 py-0.5 rounded text-xs">{children}</code>,
                            a: ({ href, children }) => <a href={href} className="text-blue-400 hover:text-blue-300 underline">{children}</a>,
                            h1: ({ children }) => <h1 className="text-lg font-bold text-white mb-2">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-base font-bold text-white mb-2">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-sm font-semibold text-white mb-1">{children}</h3>,
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    )}
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

            {/* Chat Input */}
            <div className="p-4 border-t border-gray-700 bg-gray-800">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask AUBS about your brief..."
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
              <p className="text-xs text-gray-400 mt-2">Suggestions: "What's most urgent?" • "Show me today's deadlines" • "What can I delegate?"</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
