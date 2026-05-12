import json
import argparse
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class DurationAwareVoiceClassifier:
    def __init__(self) -> None:
        from faster_whisper import WhisperModel

        self.model = WhisperModel("tiny", device="cpu", compute_type="int8")

    def sampling_plan(self, duration: float) -> tuple[int, list[int]]:
        if duration <= 600:
            clip_len = max(30, int(duration))
            return clip_len, [0]

        if duration <= 1800:
            clip_len = 150
            starts = [0, int(duration * 0.25), int(duration * 0.5), int(duration * 0.75)]
        elif duration <= 5400:
            clip_len = 120
            starts = [0, int(duration * 0.2), int(duration * 0.4), int(duration * 0.6), int(duration * 0.8)]
        else:
            clip_len = 100
            starts = [0, int(duration * 0.15), int(duration * 0.3), int(duration * 0.5), int(duration * 0.7), int(duration * 0.85)]

        max_start = max(0, int(duration) - clip_len)
        normalized = sorted({min(max(0, s), max_start) for s in starts})
        return clip_len, normalized

    def analyze(self, audio_path: Path, duration: float) -> dict:
        clip_len, starts = self.sampling_plan(duration)
        clip_results = []

        for start in starts:
            end = start + clip_len
            segments, _ = self.model.transcribe(
                str(audio_path),
                language="ca",
                vad_filter=True,
                beam_size=1,
                condition_on_previous_text=False,
                clip_timestamps=f"{start},{end}",
            )
            segments = list(segments)
            speech_seconds = sum(max(0.0, seg.end - seg.start) for seg in segments)
            ratio = speech_seconds / clip_len if clip_len else 0.0
            preview = " | ".join(seg.text.strip() for seg in segments[:2] if seg.text.strip())
            clip_results.append({
                "start": start,
                "end": end,
                "speech_seconds": speech_seconds,
                "ratio": ratio,
                "preview": preview,
            })

        avg_ratio = sum(c["ratio"] for c in clip_results) / len(clip_results)
        max_ratio = max(c["ratio"] for c in clip_results)
        voiced_clips = sum(1 for c in clip_results if c["ratio"] >= 0.20)
        strong_voiced_clips = sum(1 for c in clip_results if c["ratio"] >= 0.30)
        total_sampled_speech = sum(c["speech_seconds"] for c in clip_results)
        sampled_seconds = clip_len * len(clip_results)

        if duration <= 600:
            label = "voice" if (total_sampled_speech >= 120 or avg_ratio >= 0.30) else "noise_or_music"
        else:
            label = "voice" if (
                total_sampled_speech >= 180
                or avg_ratio >= 0.30
                or strong_voiced_clips >= 3
                or (voiced_clips >= 3 and max_ratio >= 0.35)
            ) else "noise_or_music"

        return {
            "label": label,
            "duration": duration,
            "clip_len": clip_len,
            "sampled_seconds": sampled_seconds,
            "avg_ratio": avg_ratio,
            "max_ratio": max_ratio,
            "voiced_clips": voiced_clips,
            "strong_voiced_clips": strong_voiced_clips,
            "total_sampled_speech": total_sampled_speech,
            "clips": clip_results,
        }


def build_default_sample(index: list[dict]) -> list[dict]:
    ordered = sorted(index, key=lambda x: x.get("duration") or 0)
    candidates = [
        ordered[0],
        ordered[1],
        ordered[len(ordered) // 2],
        ordered[len(ordered) // 2 + 1],
        ordered[-2],
        ordered[-1],
    ]

    special_id = "uO2Zw1eN2b4"
    special = next((item for item in index if item["id"] == special_id), None)
    if special is not None:
        candidates.append(special)

    sample = []
    seen_ids = set()
    for item in candidates:
        if item["id"] in seen_ids:
            continue
        seen_ids.add(item["id"])
        sample.append(item)
    return sample


def write_sample_report(index: list[dict], classifier: DurationAwareVoiceClassifier, report_path: Path) -> None:
    sample = build_default_sample(index)
    lines = [
        "label\tid\tduration\tclip_len\tsampled_seconds\ttotal_sampled_speech\tavg_ratio\tmax_ratio\tvoiced_clips\tstrong_voiced_clips\ttitle\tclip_summaries"
    ]

    for item in sample:
        audio_path = BASE_DIR / item["path"]
        result = classifier.analyze(audio_path, float(item.get("duration") or 0.0))
        clip_summaries = " || ".join(
            f"{clip['start']}-{clip['end']}:{clip['speech_seconds']:.1f}s/{clip['ratio']:.2f}:{clip['preview'][:60]}"
            for clip in result["clips"]
        )
        lines.append(
            f"{result['label']}\t{item['id']}\t{result['duration']:.1f}\t{result['clip_len']}\t{result['sampled_seconds']}\t"
            f"{result['total_sampled_speech']:.1f}\t{result['avg_ratio']:.2f}\t{result['max_ratio']:.2f}\t{result['voiced_clips']}\t{result['strong_voiced_clips']}\t"
            f"{item['title'].replace(chr(9), ' ')}\t{clip_summaries.replace(chr(9), ' ')}"
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def filter_index(
    source_index: Path = BASE_DIR / "index_limpio.json",
    output_index: Path = BASE_DIR / "index.json",
    sample_report: Path = BASE_DIR / "voice_validation_sample.tsv",
    decisions_report: Path = BASE_DIR / "voice_filter_decisions.tsv",
) -> None:
    index = json.load(source_index.open("r", encoding="utf-8"))
    classifier = DurationAwareVoiceClassifier()

    kept = []
    decision_lines = [
        "label\tid\tduration\tclip_len\tsampled_seconds\ttotal_sampled_speech\tavg_ratio\tmax_ratio\tvoiced_clips\tstrong_voiced_clips\ttitle"
    ]

    total_items = len(index)
    for position, item in enumerate(index, start=1):
        remaining = total_items - position
        print(
            f"[{position}/{total_items}] Procesando {item['id']} ({remaining} restantes)"
            f" | duracion={item.get('duration')}s"
        )

        audio_path = BASE_DIR / item["path"]
        result = classifier.analyze(audio_path, float(item.get("duration") or 0.0))
        print(
            f"    -> {result['label']}"
            f" | sampled={result['sampled_seconds']}s"
            f" | speech={result['total_sampled_speech']:.1f}s"
            f" | avg_ratio={result['avg_ratio']:.2f}"
            f" | max_ratio={result['max_ratio']:.2f}"
        )

        decision_lines.append(
            f"{result['label']}\t{item['id']}\t{result['duration']:.1f}\t{result['clip_len']}\t{result['sampled_seconds']}\t"
            f"{result['total_sampled_speech']:.1f}\t{result['avg_ratio']:.2f}\t{result['max_ratio']:.2f}\t{result['voiced_clips']}\t{result['strong_voiced_clips']}\t"
            f"{item['title'].replace(chr(9), ' ')}"
        )
        if result["label"] == "voice":
            kept.append(item)

    output_index.write_text(json.dumps(kept, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    decisions_report.write_text("\n".join(decision_lines) + "\n", encoding="utf-8")
    write_sample_report(index, classifier, sample_report)

    print(f"Entradas de entrada: {len(index)}")
    print(f"Entradas conservadas en index.json: {len(kept)}")
    print(f"Decisiones escritas en: {decisions_report}")
    print(f"Muestra escrita en: {sample_report}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filtra audios con Whisper para conservar voz hablada.")
    parser.add_argument("--source", default="index_limpio.json")
    parser.add_argument("--output", default="index.json")
    parser.add_argument("--sample-report", default="voice_validation_sample.tsv")
    parser.add_argument("--decisions-report", default="voice_filter_decisions.tsv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    filter_index(
        source_index=BASE_DIR / args.source,
        output_index=BASE_DIR / args.output,
        sample_report=BASE_DIR / args.sample_report,
        decisions_report=BASE_DIR / args.decisions_report,
    )


if __name__ == "__main__":
    main()
