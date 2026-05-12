import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import index_gen
import limpiar_dataset
import sync_index


BASE_DIR = Path(__file__).resolve().parent
CHANNEL_URL = "https://www.youtube.com/@AMULTIMEDIATV/videos"


def require_command(command: str) -> None:
    if shutil.which(command) is None:
        raise SystemExit(f"Error: {command} no esta disponible en PATH.")


def run_download(args: argparse.Namespace) -> None:
    require_command("yt-dlp")
    require_command("ffmpeg")

    output_dir = BASE_DIR / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "-f",
        "ba",
        "-x",
        "--audio-format",
        "mp3",
        "--yes-playlist",
        "--js-runtimes",
        "node",
        "--remote-components",
        "ejs:github",
        "--download-archive",
        str(BASE_DIR / args.archive),
        "--print-to-file",
        '{"id": %(id)j, "title": %(title)j, "duration": %(duration)j, "path": "'
        + args.output_dir.replace("\\", "/")
        + '/%(id)s.mp3"}',
        str(BASE_DIR / args.raw_index),
        "-o",
        str(output_dir / "%(id)s.%(ext)s"),
    ]

    if args.cookies_from_browser:
        cmd.extend(["--cookies-from-browser", args.cookies_from_browser])
    elif args.cookies_file:
        cmd.extend(["--cookies", str(Path(args.cookies_file).expanduser())])

    cmd.append(args.channel_url)
    subprocess.run(cmd, cwd=BASE_DIR, check=True)


def run_index(_: argparse.Namespace) -> None:
    index_gen.main()
    sync_index.main()


def run_clean(args: argparse.Namespace) -> None:
    limpiar_dataset.limpiar_y_sumar(
        json_input=args.index,
        output_folder=args.output_dir,
        min_duracion=args.min_duration,
    )


def run_voice(args: argparse.Namespace) -> None:
    import voice_filter

    voice_filter.filter_index(
        source_index=BASE_DIR / args.source,
        output_index=BASE_DIR / args.output,
        sample_report=BASE_DIR / args.sample_report,
        decisions_report=BASE_DIR / args.decisions_report,
    )


def run_all(args: argparse.Namespace) -> None:
    run_download(args)
    run_index(args)
    run_clean(args)
    if args.with_voice:
        args.source = args.voice_source
        args.output = args.voice_output
        args.sample_report = args.sample_report
        args.decisions_report = args.decisions_report
        run_voice(args)


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def interactive_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    print("Selecciona una accion:")
    print("  1. Descargar canal")
    print("  2. Generar indice")
    print("  3. Limpiar audios cortos")
    print("  4. Filtrar por voz")
    print("  5. Ejecutar descarga + indice + limpieza")
    choice = ask("Opcion", "5")

    command_by_choice = {
        "1": "download",
        "2": "index",
        "3": "clean",
        "4": "voice",
        "5": "all",
    }
    command = command_by_choice.get(choice, choice)

    argv = [command]
    if command in {"download", "all"}:
        browser = ask("Cookies desde navegador (chrome/firefox/edge, vacio para fichero)", "")
        if browser:
            argv.extend(["--cookies-from-browser", browser])
        else:
            cookies_file = ask("Fichero de cookies", "cookies.txt")
            if cookies_file:
                argv.extend(["--cookies-file", cookies_file])

    if command == "all":
        with_voice = ask("Filtrar por voz al final? (s/N)", "N").lower()
        if with_voice in {"s", "si", "y", "yes"}:
            argv.append("--with-voice")

    return parser.parse_args(argv)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ejecutor unico para descargar y preparar el dataset de AMULTIMEDIATV."
    )
    subparsers = parser.add_subparsers(dest="command")

    def add_download_options(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--channel-url", default=CHANNEL_URL)
        command_parser.add_argument("--cookies-from-browser", default="")
        command_parser.add_argument("--cookies-file", default="cookies.txt")
        command_parser.add_argument("--output-dir", default="mp3_by_id")
        command_parser.add_argument("--raw-index", default="index_raw.jsonl")
        command_parser.add_argument("--archive", default="download_archive.txt")

    download_parser = subparsers.add_parser("download", help="Descarga los MP3 del canal.")
    add_download_options(download_parser)
    download_parser.set_defaults(func=run_download)

    index_parser = subparsers.add_parser("index", help="Genera y sincroniza index.json.")
    index_parser.set_defaults(func=run_index)

    clean_parser = subparsers.add_parser("clean", help="Elimina audios cortos y crea index_limpio.json.")
    clean_parser.add_argument("--index", default="index.json")
    clean_parser.add_argument("--output-dir", default="mp3_by_id")
    clean_parser.add_argument("--min-duration", type=int, default=60)
    clean_parser.set_defaults(func=run_clean)

    voice_parser = subparsers.add_parser("voice", help="Filtra audios sin voz hablada.")
    voice_parser.add_argument("--source", default="index_limpio.json")
    voice_parser.add_argument("--output", default="index.json")
    voice_parser.add_argument("--sample-report", default="voice_validation_sample.tsv")
    voice_parser.add_argument("--decisions-report", default="voice_filter_decisions.tsv")
    voice_parser.set_defaults(func=run_voice)

    all_parser = subparsers.add_parser("all", help="Ejecuta descarga, indice y limpieza.")
    add_download_options(all_parser)
    all_parser.add_argument("--min-duration", type=int, default=60)
    all_parser.add_argument("--index", default="index.json")
    all_parser.add_argument("--with-voice", action="store_true")
    all_parser.add_argument("--voice-source", default="index_limpio.json")
    all_parser.add_argument("--voice-output", default="index.json")
    all_parser.add_argument("--sample-report", default="voice_validation_sample.tsv")
    all_parser.add_argument("--decisions-report", default="voice_filter_decisions.tsv")
    all_parser.set_defaults(func=run_all)

    return parser


def main() -> None:
    parser = build_parser()
    args = interactive_args(parser) if len(sys.argv) == 1 else parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        raise SystemExit(1)

    try:
        args.func(args)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc


if __name__ == "__main__":
    main()
