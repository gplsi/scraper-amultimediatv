import json
from collections import defaultdict
from pathlib import Path


FULLWIDTH_REPLACEMENTS = str.maketrans({
    '"': "＂",
    "*": "＊",
    "/": "／",
    ":": "：",
    "<": "＜",
    ">": "＞",
    "?": "？",
    "\\": "＼",
    "|": "｜",
})

JSON_PATH = Path("index.json")
MP3_DIR = Path("mp3_by_id")


def normalize_name(path_str: str) -> str:
    return Path(path_str).name.translate(FULLWIDTH_REPLACEMENTS)


def main() -> None:
    with JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    by_normalized_name = defaultdict(list)
    for item in data:
        raw_path = item.get("path")
        if raw_path:
            by_normalized_name[normalize_name(raw_path)].append(item)

    synced = []
    for mp3_file in sorted(MP3_DIR.glob("*.mp3"), key=lambda p: p.name.lower()):
        matches = by_normalized_name.get(mp3_file.name, [])
        if matches:
            item = dict(matches[0])
        else:
            item = {
                "title": mp3_file.stem,
                "duration": None,
                "path": str(Path("mp3_by_id") / mp3_file.name),
            }

        item["path"] = str(Path("mp3_by_id") / mp3_file.name)
        synced.append(item)

    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(synced, f, indent=4, ensure_ascii=False)

    print(f"index.json actualizado con {len(synced)} entradas únicas")


if __name__ == "__main__":
    main()
