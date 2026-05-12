import json
from pathlib import Path


RAW_INDEX = Path("index_raw.jsonl")
FINAL_INDEX = Path("index.json")
MP3_DIR = Path("mp3_by_id")


def load_latest_entries_by_id() -> dict[str, dict]:
    latest_by_id: dict[str, dict] = {}

    with RAW_INDEX.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Línea inválida en {RAW_INDEX}:{line_number}"
                ) from exc

            video_id = entry.get("id")
            if not video_id:
                continue

            latest_by_id[video_id] = {
                "id": video_id,
                "title": entry.get("title") or video_id,
                "duration": entry.get("duration"),
                "path": f"mp3_by_id/{video_id}.mp3",
                "filename": f"{video_id}.mp3",
            }

    return latest_by_id


def main() -> None:
    latest_by_id = load_latest_entries_by_id()
    disk_files = sorted(MP3_DIR.glob("*.mp3"), key=lambda p: p.name.lower())

    data = []
    for mp3_file in disk_files:
        video_id = mp3_file.stem
        entry = latest_by_id.get(
            video_id,
            {
                "id": video_id,
                "title": video_id,
                "duration": None,
                "path": f"mp3_by_id/{mp3_file.name}",
                "filename": mp3_file.name,
            },
        )
        entry["path"] = f"mp3_by_id/{mp3_file.name}"
        entry["filename"] = mp3_file.name
        data.append(entry)

    missing_mp3_ids = sorted(set(latest_by_id) - {p.stem for p in disk_files})

    with FINAL_INDEX.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Índice generado con {len(data)} entradas.")
    print(f"IDs con metadata pero sin MP3 en disco: {len(missing_mp3_ids)}")
    if missing_mp3_ids:
        print("Primeros IDs faltantes:", ", ".join(missing_mp3_ids[:10]))


if __name__ == "__main__":
    main()
