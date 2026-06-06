"use client";

import { useState, useEffect, useRef } from "react";
import Header from "@/components/Header";
import Disclaimer from "@/components/Disclaimer";
import Sidebar from "@/components/Sidebar";
import ChatInput from "@/components/ChatInput";
import ChatMessage from "@/components/ChatMessage";
import ExampleQuestions from "@/components/ExampleQuestions";
import { sendMessage, getCategories, Category, ChatResponse, HistoryMessage } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "bot";
  content: string;
  data?: ChatResponse;
  timestamp: Date;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load categories on mount
  useEffect(() => {
    getCategories()
      .then(setCategories)
      .catch(() => {
        // Fallback categories if API is down
        setCategories([
          { category: "Large Cap", icon: "📈", subtitle: "Stability & steady growth", funds: [] },
          { category: "Mid Cap", icon: "📊", subtitle: "Balanced risk-reward", funds: [] },
          { category: "Small Cap", icon: "🚀", subtitle: "High potential volatility", funds: [] },
          { category: "Flexi Cap / Focused", icon: "🎯", subtitle: "Diversified allocation", funds: [] },
          { category: "Defence", icon: "🛡️", subtitle: "Sector specific focus", funds: [] },
          { category: "Equity / Thematic", icon: "🏛️", subtitle: "Pure stock-based funds", funds: [] },
        ]);
      });
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // Build conversation history from existing messages (exclude the message just added)
    const history: HistoryMessage[] = messages.map((msg) => ({
      role: msg.role === "user" ? "user" : "bot",
      content: msg.content,
    }));

    try {
      const response = await sendMessage(text, history);
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "bot",
        content: response.answer,
        data: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "bot",
        content: "Sorry, I'm having trouble connecting to the server. Please make sure the backend is running on port 8000.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFundClick = (fundName: string) => {
    setInputValue(`Tell me about ${fundName}`);
  };

  const handleExampleClick = (question: string) => {
    setInputValue(question);
  };

  const handleNewChat = () => {
    setMessages([]);
    setInputValue("");
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Disclaimer />
      <Header onNewChat={handleNewChat} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar categories={categories} onFundClick={handleFundClick} />

        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-6">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-7 h-7 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-800 mb-2">
                  Mutual Fund FAQ Assistant
                </h2>
                <p className="text-sm text-gray-500 max-w-md mb-6">
                  I provide objective data from 60 mutual funds on Groww. Ask about NAV, expense ratio, exit load, fund managers, and more.
                </p>
                <ExampleQuestions onQuestionClick={handleExampleClick} />
              </div>
            ) : (
              <div className="max-w-3xl mx-auto">
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}

                {isLoading && (
                  <div className="flex gap-3 mb-4">
                    <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
                      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div className="bg-gray-50 rounded-xl px-4 py-3">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]"></span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSend}
            disabled={isLoading}
          />

          <div className="bg-white border-t border-gray-100 px-6 py-2 flex items-center justify-between text-xs text-gray-400">
            <span>© 2026 MF Assistant. Information provided is for educational purposes only.</span>
            <div className="flex gap-4">
              <span className="hover:text-gray-600 cursor-pointer">Privacy Policy</span>
              <span className="hover:text-gray-600 cursor-pointer">Terms of Service</span>
              <span className="hover:text-gray-600 cursor-pointer">Data Sources</span>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
