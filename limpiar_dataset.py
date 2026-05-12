import json
import os
from pathlib import Path


def resolve_mp3_path(raw_path: str | None, output_folder: str) -> Path | None:
    if not raw_path:
        return None

    candidate = Path(raw_path)
    if candidate.exists():
        return candidate

    candidate = Path(output_folder) / Path(raw_path).name
    if candidate.exists():
        return candidate

    return None


def limpiar_y_sumar(
    json_input: str = "index.json",
    output_folder: str = "mp3_by_id",
    min_duracion: int = 60,
) -> None:
    json_path = Path(json_input)
    output_dir = Path(output_folder)

    if not json_path.exists():
        print(f"Error: No se encuentra el archivo {json_input}")
        return

    if not output_dir.exists():
        print(f"Error: No se encuentra la carpeta {output_folder}")
        return

    with json_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: El formato del JSON no es válido.")
            return

    seen_ids = set()
    nuevo_index = []
    segundos_totales = 0
    eliminados = 0
    no_encontrados = 0
    duplicados_descartados = 0

    for item in data:
        video_id = item.get("id") or Path(item.get("path", "")).stem
        if video_id in seen_ids:
            duplicados_descartados += 1
            continue
        seen_ids.add(video_id)

        duracion = item.get("duration")
        duracion = duracion if isinstance(duracion, (int, float)) else 0

        if duracion >= min_duracion:
            item["id"] = video_id
            item["filename"] = f"{video_id}.mp3"
            item["path"] = f"{output_folder}/{video_id}.mp3"
            nuevo_index.append(item)
            segundos_totales += duracion
            continue

        file_path = resolve_mp3_path(item.get("path"), str(output_dir))
        if file_path is not None:
            os.remove(file_path)
            eliminados += 1
        else:
            no_encontrados += 1

    with Path("index_limpio.json").open("w", encoding="utf-8") as f:
        json.dump(nuevo_index, f, indent=4, ensure_ascii=False)

    minutos_totales = segundos_totales / 60
    print("-" * 30)
    print("LIMPIEZA COMPLETADA")
    print("-" * 30)
    print(f"Duplicados descartados del índice: {duplicados_descartados}")
    print(f"Audios eliminados del disco (< {min_duracion} s): {eliminados}")
    print(f"Audios cortos no encontrados en disco: {no_encontrados}")
    print(f"Audios restantes en el índice: {len(nuevo_index)}")
    print(f"Duración total del dataset: {minutos_totales:.2f} minutos")
    print("Archivo 'index_limpio.json' generado con éxito.")


if __name__ == "__main__":
    limpiar_y_sumar()
