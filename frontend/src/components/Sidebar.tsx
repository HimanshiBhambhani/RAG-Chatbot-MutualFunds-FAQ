"use client";

import { useState } from "react";
import { Category } from "@/lib/api";

interface SidebarProps {
  categories: Category[];
  onFundClick: (fundName: string) => void;
}

export default function Sidebar({ categories, onFundClick }: SidebarProps) {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(
    "Defence"
  );

  const toggleCategory = (category: string) => {
    setExpandedCategory(expandedCategory === category ? null : category);
  };

  return (
    <aside className="w-80 bg-white border-r border-gray-100 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-gray-800">Quick Categories</h2>
        <p className="text-xs text-gray-500 mt-0.5">Explore common fund types</p>
      </div>

      {/* Category List */}
      <div className="flex-1 overflow-y-auto px-3 py-2">
        {categories.map((cat) => (
          <div key={cat.category} className="mb-1.5">
            {/* Category Header */}
            <button
              onClick={() => toggleCategory(cat.category)}
              className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 hover:bg-gray-50 ${
                expandedCategory === cat.category
                  ? "bg-emerald-50 border-l-3 border-emerald-500"
                  : "border-l-3 border-transparent"
              }`}
            >
              <span className="text-xl flex-shrink-0">{cat.icon}</span>
              <div className="flex-1 text-left">
                <p className={`text-sm font-medium ${
                  expandedCategory === cat.category
                    ? "text-emerald-700"
                    : "text-gray-700"
                }`}>
                  {cat.category}
                </p>
                <p className="text-xs text-gray-400">{cat.subtitle}</p>
              </div>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
                  expandedCategory === cat.category ? "rotate-180" : ""
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Expanded Fund List */}
            {expandedCategory === cat.category && (
              <div className="ml-10 mt-1 mb-2 max-h-40 overflow-y-auto scrollbar-thin">
                {cat.funds.map((fund) => (
                  <button
                    key={fund.slug}
                    onClick={() => onFundClick(fund.name)}
                    className="w-full text-left px-3 py-2 text-sm text-gray-600 rounded-lg hover:bg-emerald-50 hover:text-emerald-700 hover:border-l-2 hover:border-emerald-400 transition-all duration-150 truncate"
                    title={fund.name}
                  >
                    {fund.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Quick Tip */}
      <div className="p-4 m-3 bg-amber-50 rounded-xl border border-amber-100">
        <p className="text-xs font-medium text-amber-700">💡 Quick Tip</p>
        <p className="text-xs text-amber-600 mt-1">
          Ask about &quot;Expense Ratio&quot; or &quot;Portfolio Turnover&quot; for any fund to understand hidden costs.
        </p>
      </div>
    </aside>
  );
}
