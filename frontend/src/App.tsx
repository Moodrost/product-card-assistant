import { useEffect, useRef, useState } from "react";
import { generateCard, getHealth } from "./api";
import type { CardResult, Health } from "./api";
import { examples } from "./examples";

type View = "preview" | "markdown" | "json";

export function App() {
  const [input, setInput] = useState(JSON.stringify(examples[0], null, 2));
  const [result, setResult] = useState<CardResult | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<View>("preview");
  const [dirty, setDirty] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const resultHeading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((h) => {
        if (active) setHealth(h);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
      controller.current?.abort();
    };
  }, []);

  function edit(value: string) {
    setInput(value);
    setError("");
    setNotice("");
    setDirty(result !== null);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    let product: unknown;
    try {
      product = JSON.parse(input);
    } catch {
      setError("Некорректный JSON. Проверьте кавычки, запятые и скобки.");
      return;
    }
    controller.current = new AbortController();
    const timeout = window.setTimeout(() => controller.current?.abort(), 75000);
    setBusy(true);
    try {
      const next = await generateCard(product, controller.current.signal);
      setResult(next);
      setDirty(false);
      setView("preview");
      window.setTimeout(() => resultHeading.current?.focus(), 0);
    } catch (e) {
      setError(
        e instanceof Error && e.name === "AbortError"
          ? "Время ожидания истекло. Проверьте сервер и повторите запрос."
          : e instanceof TypeError
            ? "Не удалось связаться с сервером. Проверьте подключение."
            : e instanceof Error
              ? e.message
              : "Не удалось подготовить карточку. Повторите запрос.",
      );
    } finally {
      window.clearTimeout(timeout);
      setBusy(false);
      controller.current = null;
    }
  }

  async function copy(format: "markdown" | "json") {
    if (!result) return;
    const text =
      format === "markdown" ? result.markdown : JSON.stringify(result, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      setNotice(`${format === "markdown" ? "Markdown" : "JSON"} скопирован.`);
    } catch {
      setNotice(
        "Не удалось скопировать. Откройте нужный формат и выделите текст вручную.",
      );
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a href="/" className="brand" aria-label="Карточка, главная">
          <span className="brand-mark" aria-hidden="true" />
          Карточка<span className="brand-detail">редактор каталога</span>
        </a>
        <span className="mode">
          {health
            ? health.mode === "demo"
              ? "Демо · без LLM"
              : health.configured
                ? "API-ключ настроен"
                : "Нужен API-ключ"
            : "Проверяем сервер…"}
        </span>
      </header>
      <main>
        <div className="page-heading">
          <h1>От параметров — к описанию.</h1>
          <p>
            Подготовьте черновик для B2B-каталога. Характеристики останутся
            такими, какими вы их передали.
          </p>
        </div>
        {health?.mode === "demo" && (
          <div className="banner">
            Сейчас включён деморежим: результат собирается локально, без вызова
            модели. Второй пример содержит вымышленные данные.
          </div>
        )}
        {health && !health.configured && (
          <div className="banner">
            Для генерации задайте OPENAI_API_KEY в файле .env на сервере и
            перезапустите API. Для просмотра без ключа используйте
            CARD_MODE=demo.
          </div>
        )}
        <div className="workspace">
          <section className="input-panel" aria-labelledby="input-heading">
            <div className="panel-heading">
              <h2 id="input-heading">Исходные данные</h2>
              <span>JSON</span>
            </div>
            <p className="hint">
              Один товар за раз. Пустое значение обозначьте как null.
            </p>
            <div className="examples" aria-label="Загрузить пример">
              <span>Попробовать:</span>
              <button
                type="button"
                disabled={busy}
                onClick={() => edit(JSON.stringify(examples[0], null, 2))}
              >
                Манометр
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => edit(JSON.stringify(examples[1], null, 2))}
              >
                Термометр · демо
              </button>
            </div>
            <form onSubmit={submit}>
              <label htmlFor="product-json" className="visually-hidden">
                Данные товара в формате JSON
              </label>
              <textarea
                id="product-json"
                spellCheck={false}
                value={input}
                disabled={busy}
                onChange={(e) => edit(e.target.value)}
                aria-describedby="input-help"
              />
              <p id="input-help" className="hint">
                Обязательно только название. Для хорошего черновика добавьте
                производителя, параметры и назначение.
              </p>
              {error && (
                <div className="error" role="alert">
                  {error}
                </div>
              )}
              <button
                className="primary"
                disabled={busy || health?.configured === false}
                type="submit"
              >
                {busy ? "Готовим черновик…" : "Подготовить карточку"}
                <svg
                  aria-hidden="true"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <path d="M5 12h14m-6-6 6 6-6 6" />
                </svg>
              </button>
              <p className="privacy">
                {health?.mode === "demo"
                  ? "Данные обрабатываются локально."
                  : "В режиме LLM данные товара отправляются в OpenAI API."}{" "}
                API-ключ хранится только на сервере.
              </p>
            </form>
          </section>
          <section
            className="output-panel"
            aria-labelledby="output-heading"
            aria-busy={busy}
          >
            <div className="panel-heading">
              <h2 id="output-heading" ref={resultHeading} tabIndex={-1}>
                Черновик карточки
              </h2>
              <span>{result ? "Нужна проверка" : "Предпросмотр"}</span>
            </div>
            {dirty && (
              <div className="banner stale">
                Исходные данные изменились. Подготовьте карточку заново перед
                копированием.
              </div>
            )}
            {!result ? (
              <div className="empty">
                <div className="empty-sheet" aria-hidden="true">
                  <div />
                  <div />
                  <div />
                  <div />
                </div>
                <h3>
                  {busy
                    ? "Собираем карточку из ваших данных"
                    : "Здесь появится готовый черновик"}
                </h3>
                <p>
                  Описание, характеристики, поисковые запросы и подсказка для
                  менеджера — в одной карточке.
                </p>
                <p className="empty-note">
                  Без выдуманных значений. С пометками о пробелах.
                </p>
              </div>
            ) : (
              <>
                <div className="result-toolbar">
                  <div className="view-switch" aria-label="Формат результата">
                    {(["preview", "markdown", "json"] as const).map((v) => (
                      <button
                        key={v}
                        type="button"
                        aria-pressed={view === v}
                        onClick={() => setView(v)}
                      >
                        {v === "preview"
                          ? "Карточка"
                          : v === "markdown"
                            ? "Markdown"
                            : "JSON"}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="copy"
                    disabled={dirty || busy}
                    onClick={() => copy(view === "json" ? "json" : "markdown")}
                  >
                    Копировать {view === "json" ? "JSON" : "Markdown"}
                  </button>
                </div>
                {view !== "preview" ? (
                  <pre className="raw-output" tabIndex={0}>
                    {view === "json"
                      ? JSON.stringify(result, null, 2)
                      : result.markdown}
                  </pre>
                ) : (
                  <article className="card-preview">
                    <div className="section-label">
                      <h3>SEO-заголовок</h3>
                      <span>{result.meta.title_length} / 70</span>
                    </div>
                    <p className="seo-title">{result.card.seo_title}</p>
                    <div className="section-label">
                      <h3>SEO-описание</h3>
                      <span>{result.meta.description_length} символов</span>
                    </div>
                    <p className="description">{result.card.seo_description}</p>
                    <h3>Ключевые характеристики</h3>
                    <table>
                      <tbody>
                        {result.card.characteristics.map((c, i) => (
                          <tr key={i}>
                            <th scope="row">{c.name}</th>
                            <td className={c.source ? "" : "missing-value"}>
                              {c.value}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <h3>Поисковые запросы</h3>
                    <ul className="queries">
                      {result.card.search_queries.map((q) => (
                        <li key={q}>{q}</li>
                      ))}
                    </ul>
                    <h3>Для менеджера</h3>
                    <div className="commercial">
                      <p>{result.card.commercial.audience}</p>
                      <p>{result.card.commercial.task}</p>
                      <p className="hint">{result.card.commercial.caveat}</p>
                    </div>
                    <div className="review">
                      <h3>Перед публикацией</h3>
                      <ul>
                        {result.card.missing_fields.map((m) => (
                          <li key={m.field}>{m.message}</li>
                        ))}
                        {result.card.warnings.map((w) => (
                          <li key={w}>{w}</li>
                        ))}
                      </ul>
                    </div>
                    {result.card.source_description && (
                      <details className="source-description">
                        <summary>Полное исходное описание для сверки</summary>
                        <p className="description">
                          {result.card.source_description}
                        </p>
                      </details>
                    )}
                  </article>
                )}
              </>
            )}
            <div className="sr-status" role="status" aria-live="polite">
              {notice || (busy ? "Подготовка карточки…" : "")}
            </div>
          </section>
        </div>
        <footer>
          Черновик помогает подготовить контент. Проверку по паспорту и решение
          о публикации принимает редактор.
          <a href="/docs" target="_blank" rel="noreferrer">
            Документация API
          </a>
        </footer>
      </main>
    </div>
  );
}
