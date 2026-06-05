"use client";

import { ChatResponse } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "bot";
  content: string;
  data?: ChatResponse;
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-md bg-emerald-500 text-white px-4 py-3 rounded-2xl rounded-tr-md shadow-sm">
          <p className="text-sm">{message.content}</p>
        </div>
      </div>
    );
  }

  // Bot message
  const data = message.data;
  const isNoInfoResponse = message.content.toLowerCase().includes("i don't have this information") ||
    message.content.toLowerCase().includes("don't have this information");
  const showFundCard = data?.fund_name && !data.blocked_by && !isNoInfoResponse;

  return (
    <div className="flex gap-3 mb-6">
      {/* Bot avatar */}
      <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0 mt-1">
        <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>

      {/* Message content */}
      <div className="max-w-2xl">
        {/* Fund card (if structured data available) */}
        {showFundCard && (
          <div className="bg-white border border-gray-200 rounded-xl p-4 mb-2 shadow-sm">
            <h3 className="font-semibold text-gray-800 text-base mb-3">{data.fund_name}</h3>

            {/* Render the answer */}
            <div className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
              {formatAnswer(data.answer)}
            </div>

            {/* Source link */}
            {data.source_url && (
              <a
                href={data.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-emerald-600 hover:text-emerald-700 mt-3 font-medium"
              >
                View on Groww
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            )}

            {/* Last updated */}
            {data.last_updated && (
              <p className="text-xs text-gray-400 mt-2">
                Last updated: {data.last_updated}
              </p>
            )}
          </div>
        )}

        {/* Plain text response (for guardrail blocks, no fund_name, or no-info) */}
        {!showFundCard && (
          <div className="bg-gray-50 rounded-xl px-4 py-3">
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              {message.content}
            </p>
          </div>
        )}

        {/* Feedback */}
        {showFundCard && (
          <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
            <span>Was this helpful?</span>
            <button className="hover:text-emerald-500 transition-colors">👍</button>
            <button className="hover:text-red-400 transition-colors">👎</button>
          </div>
        )}
      </div>
    </div>
  );
}

function formatAnswer(answer: string): string {
  // Remove Source: line and Last updated line (shown separately in UI)
  return answer
    .replace(/\n*Source:.*$/m, "")
    .replace(/\n*Last updated from sources:.*$/m, "")
    .trim();
}
