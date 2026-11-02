"""Export examples from the running API, retaining real demo/live metadata."""

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Сохранить результаты двух примеров из работающего API"
    )
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=Path("examples/results"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    products = json.loads((root / "examples/products.json").read_text(encoding="utf-8"))
    results = []
    for i, product in enumerate(products, start=1):
        request = Request(
            args.url.rstrip("/") + "/api/generate",
            data=json.dumps(product, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=75) as response:
                result = json.load(response)
        except HTTPError as exc:
            parser.exit(
                1, f"API вернул {exc.code}. Проверьте настройки сервера и повторите запрос.\n"
            )
        except URLError:
            parser.exit(1, "Не удалось связаться с API. Сначала запустите сервер.\n")
        results.append((i, result))
    # Write only after both requests succeed, to avoid a half-updated example set.
    args.output.mkdir(parents=True, exist_ok=True)
    for i, result in results:
        (args.output / f"product-{i}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        provenance = (
            f"> Режим: {result['meta']['mode']}; вызов LLM: "
            f"{'да' if result['meta']['llm_called'] else 'нет'}. "
            "Источник входа: examples/products.json.\n\n"
        )
        (args.output / f"product-{i}.md").write_text(
            provenance + result["markdown"], encoding="utf-8"
        )
        print(
            f"product-{i}: {result['meta']['mode']}, "
            f"{result['meta']['description_length']} символов"
        )


if __name__ == "__main__":
    main()
