param(
    [string]$CookiesFromBrowser = "",
    [string]$CookiesFile = "cookies.txt"
)

$ErrorActionPreference = "Stop"

$ChannelUrl = "https://www.youtube.com/@AMULTIMEDIATV/videos"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputDir = Join-Path $ScriptRoot "mp3_by_id"
$RawIndex = Join-Path $ScriptRoot "index_raw.jsonl"

Set-Location $ScriptRoot

if (-not (Get-Command yt-dlp -ErrorAction SilentlyContinue)) {
    throw "yt-dlp no está disponible en PATH."
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw "ffmpeg no está disponible en PATH."
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$YtDlpArgs = @(
    '-f', 'ba',
    '-x',
    '--audio-format', 'mp3',
    '--yes-playlist',
    '--js-runtimes', 'node',
    '--remote-components', 'ejs:github',
    '--download-archive', 'download_archive.txt',
    '--print-to-file', '{"id": %(id)j, "title": %(title)j, "duration": %(duration)j, "path": "mp3_by_id/%(id)s.mp3"}', $RawIndex,
    '-o', 'mp3_by_id/%(id)s.%(ext)s'
)

if ($CookiesFromBrowser) {
    $YtDlpArgs += @('--cookies-from-browser', $CookiesFromBrowser)
}
elseif ($CookiesFile) {
    $YtDlpArgs += @('--cookies', $CookiesFile)
}

$YtDlpArgs += $ChannelUrl

& yt-dlp @YtDlpArgs
