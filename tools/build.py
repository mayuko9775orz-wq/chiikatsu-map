"""ちい活マップのビルド。

data/spots.json と data/basemap.json を src/template.html に埋め込んで、
  - chiikatsu-map.html … claude.ai の Artifact 用(head/body は公開時に自動で付く)
  - docs/index.html    … GitHub Pages で公開する完全なHTML
を書き出す。使い方: python tools/build.py
"""
import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATEGORIES = {"shop", "food", "facility", "limited"}
COUNTRIES = {"JP", "KR", "TW", "CN"}
REQUIRED = ("id", "name", "category", "pref")


def load_spots():
    path = ROOT / "data" / "spots.json"
    spots = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    seen, problems = set(), []
    for i, s in enumerate(spots):
        label = s.get("id") or f"#{i}"
        for key in REQUIRED:
            if not s.get(key):
                problems.append(f"{label}: {key} がありません")
        s.setdefault("country", "JP")
        if s["country"] not in COUNTRIES:
            problems.append(f"{label}: country が不正です ({s['country']})")
        if s.get("category") not in CATEGORIES:
            problems.append(f"{label}: category が不正です ({s.get('category')})")
        if s.get("id") in seen:
            problems.append(f"{label}: id が重複しています")
        seen.add(s.get("id"))
        for key in ("lat", "lng"):
            if s.get(key) is not None and not isinstance(s[key], (int, float)):
                problems.append(f"{label}: {key} は数値か null にしてください")
        if s.get("category") == "limited" and not (s.get("startDate") or s.get("endDate")):
            problems.append(f"{label}: 期間限定なのに startDate / endDate がありません")
    return spots, problems


def embed(value):
    # </script> を閉じさせないためのエスケープ
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def main():
    spots, problems = load_spots()
    if problems:
        print("データの問題:\n  " + "\n  ".join(problems))
        sys.exit(1)

    basemap = json.loads((ROOT / "data" / "basemap.json").read_text(encoding="utf-8"))
    footer = (ROOT / "src" / "footer.html").read_text(encoding="utf-8")
    data_date = json.loads((ROOT / "data" / "meta.json").read_text(encoding="utf-8"))["dataDate"]
    y, m, d = data_date.split("-")
    footer = footer.replace("__DATA_DATE__", f"{y}年{int(m)}月{int(d)}日")

    page = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    page = (page.replace("__FOOTER__", footer.strip())
                .replace("__MAP_JSON__", embed(basemap))
                .replace("__SPOTS_JSON__", embed(spots)))
    head, body = page.split("<!--BODY-->", 1)

    (ROOT / "chiikatsu-map.html").write_text(head + body, encoding="utf-8")

    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        + head.strip() + "\n</head>\n<body>\n" + body.strip() + "\n</body>\n</html>\n",
        encoding="utf-8",
    )
    counts = {}
    for s in spots:
        counts[s["country"]] = counts.get(s["country"], 0) + 1
    print(f"ビルド完了: {len(spots)}か所 {counts} / データ時点 {data_date} / {datetime.date.today()}")


if __name__ == "__main__":
    main()
