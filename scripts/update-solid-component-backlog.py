#!/usr/bin/env python3
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "frontend-solid" / "src" / "pages"
OUTPUT_FILE = ROOT / "frontend-solid" / "component-backlog.json"

IMPORT_PATTERN = re.compile(
    r'import\s+\{([^}]+)\}\s+from\s+"../components/(ui|states)/([^"]+)";'
)

SUGGESTED_NEXT_COMPONENTS = [
    {
        "name": "ConfirmDialog",
        "status": "planned",
        "reason": "Admin tarafindaki silme aksiyonlarinda standard onay penceresi gerekir.",
    },
    {
        "name": "FormField",
        "status": "planned",
        "reason": "Input + label + hata metni tekrarlarini tek bir komponentte toplar.",
    },
    {
        "name": "DataTable",
        "status": "planned",
        "reason": "Admin listelerinde kolon/siralama/aksiyon yapisini sade bir yapida birlestirir.",
    },
]


def collect_usage():
    usage = Counter()
    pages = []

    for page_file in sorted(PAGES_DIR.glob("*.tsx")):
        content = page_file.read_text(encoding="utf-8")
        page_components = set()
        for names_chunk, group_name, _ in IMPORT_PATTERN.findall(content):
            _ = group_name
            names = [name.strip() for name in names_chunk.split(",")]
            for name in names:
                if not name:
                    continue
                usage[name] += 1
                page_components.add(name)

        pages.append(
            {
                "page": page_file.name,
                "components": sorted(page_components),
            }
        )

    return usage, pages


def main():
    usage, pages = collect_usage()

    payload = {
        "generatedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "frontend-solid/src/pages/*.tsx",
        "totalPages": len(pages),
        "componentUsage": [
            {"component": component, "pageCount": count}
            for component, count in sorted(usage.items(), key=lambda item: (-item[1], item[0]))
        ],
        "pages": pages,
        "suggestedNextComponents": SUGGESTED_NEXT_COMPONENTS,
        "notes": [
            "Bu dosya scripts/update-solid-component-backlog.py ile uretilir.",
            "Yeni sayfa tasindiginda bu script tekrar calistirilmalidir.",
        ],
    }

    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] component backlog guncellendi: {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
