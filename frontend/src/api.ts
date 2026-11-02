export interface Product {
  name: string;
  manufacturer?: string | null;
  specs?: Record<string, string | null>;
  description?: string | null;
  expected_specs?: string[];
}

export interface CardResult {
  card: {
    seo_title: string;
    seo_description: string;
    characteristics: { name: string; value: string; source: string | null }[];
    search_queries: string[];
    commercial: { audience: string; task: string; caveat: string };
    missing_fields: { field: string; message: string }[];
    warnings: string[];
    source_description: string | null;
  };
  markdown: string;
  meta: {
    mode: "live" | "demo";
    llm_called: boolean;
    model: string | null;
    title_length: number;
    description_length: number;
  };
}

export interface Health {
  status: string;
  mode: "live" | "demo";
  configured: boolean;
}

export async function getHealth(): Promise<Health> {
  const response = await fetch("/api/health");
  if (!response.ok) throw new Error("Сервер недоступен. Проверьте запуск API.");
  return response.json();
}

export async function generateCard(
  product: unknown,
  signal: AbortSignal,
): Promise<CardResult> {
  const response = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(product),
    signal,
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const details = payload?.error?.details
      ?.map(
        (d: { field: string; message: string }) => `${d.field}: ${d.message}`,
      )
      .join("\n");
    throw new Error(
      [
        payload?.error?.message || `Ошибка сервера (${response.status}).`,
        details,
      ]
        .filter(Boolean)
        .join("\n"),
    );
  }
  return payload;
}
