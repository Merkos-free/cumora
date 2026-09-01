#!/usr/bin/env python3
"""Small follow-up fixes applied after finalize-russian-fork.py."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if new in text:
        return
    if text.count(old) != 1:
        raise RuntimeError(f"{path}: patch anchor not found exactly once: {old!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# Use semantic landmark/group roles instead of suppressing accessibility checks.
replace_once(
    "website/index.html",
    '<div class="product-stage" aria-label="Интерфейс Cumora на компьютере и телефоне">',
    '<div class="product-stage" role="group" aria-label="Интерфейс Cumora на компьютере и телефоне">',
)
replace_once(
    "website/index.html",
    '<div class="terminal" aria-label="Пример команд локального запуска">',
    '<div class="terminal" role="region" aria-label="Пример команд локального запуска">',
)
replace_once(
    "website/index.html",
    '<div class="platforms" aria-label="Поддерживаемые платформы">',
    '<div class="platforms" role="list" aria-label="Поддерживаемые платформы">',
)
replace_once(
    "website/index.html",
    '<span class="platform">macOS · Apple Silicon и Intel</span>',
    '<span class="platform" role="listitem">macOS · Apple Silicon и Intel</span>',
)
replace_once(
    "website/index.html",
    '<span class="platform">Windows · x64</span>',
    '<span class="platform" role="listitem">Windows · x64</span>',
)
replace_once(
    "website/index.html",
    '<span class="platform">Linux · x64</span>',
    '<span class="platform" role="listitem">Linux · x64</span>',
)

# Windows PowerShell 5.1 has no Set-Content -Encoding utf8NoBOM value.
replace_once(
    "scripts/windows/setup.ps1",
    '"@ | Set-Content -Path \'.env\' -Encoding utf8NoBOM',
    '"@\n    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)\n    [System.IO.File]::WriteAllText((Join-Path $RepoRoot \'.env\'), $envText, $utf8NoBom)',
)

# The here-string needs a variable before WriteAllText.
replace_once(
    "scripts/windows/setup.ps1",
    '    @"\nNODE_ENV=development',
    '    $envText = @"\nNODE_ENV=development',
)

print("Дополнительные правки применены.")
