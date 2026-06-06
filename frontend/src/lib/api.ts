// In production with Vercel rewrites, use relative path (empty string).
// Locally or when NEXT_PUBLIC_API_URL is set, use that URL.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface ChatResponse {
  answer: string;
  source_url: string;
  fund_name: string;
  last_updated: string;
  chunks_used: number;
  blocked_by: string;
}

export interface CategoryFund {
  name: string;
  slug: string;
}

export interface Category {
  category: string;
  icon: string;
  subtitle: string;
  funds: CategoryFund[];
}

export interface HistoryMessage {
  role: "user" | "bot";
  content: string;
}

export async function sendMessage(
  query: string,
  history: HistoryMessage[] = []
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, history }),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export async function getCategories(): Promise<Category[]> {
  const res = await fetch(`${API_BASE}/api/categories`);

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    return res.ok;
  } catch {
    return false;
  }
}
