"""
Находит нарушения стиля в комментариях и докстрингах.

Ничего не меняет - только показывает, что смотреть руками. Механическую часть чинит
normalize_chars.py, остальное требует суждения.
"""

from __future__ import annotations

import ast
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import comment_spans, docstring_nodes, targets  # noqa: E402

# Двоеточия внутри технических записей прозой не считаются.
TECHNICAL = re.compile(
    r'(https?://|[A-Za-z_]+:[A-Za-z_0-9]{2,}|\d{1,2}:\d{2}|noqa|type:|param|return)',
)
# Неудобные символы заданы кодами, а не литералами. Литерал легко превращается
# в обычную кавычку при копировании через редактор или консоль, и тогда скрипт
# начинает ругаться на нормальный ASCII.
AWKWARD = {
    '\u2014', '\u2013',                       # длинное и среднее тире
    '\u00ab', '\u00bb',                       # ёлочки
    '\u201c', '\u201d', '\u2018', '\u2019',   # кавычки-запятые
    '\u2026',                                 # многоточие
    '\u2192', '\u2190', '\u2194',             # стрелки
    '\u2264', '\u2265', '\u2260',             # <= >= !=
    '\u00b2', '\u00b3',                       # степени
    '\u20bd',                                 # рубль
    '\u00a0',                                 # неразрывный пробел
}
# Докстринг в повелительном наклонении: первое слово - глагол на -ть или -ти.
IMPERATIVE = re.compile(r'^\s*[«"\']?([А-ЯЁ][а-яё]+(?:ть|ти))\b')


def prose_colon(line: str) -> bool:
    """Проверяет, есть ли в строке двоеточие, вводящее пояснение."""
    for match in re.finditer(r':', line):
        around = line[max(0, match.start() - 14):match.start() + 14]
        if not TECHNICAL.search(around):
            return True
    return False


def report(path: Path) -> list[str]:
    """Собирает нарушения по одному файлу."""
    src = path.read_text(encoding='utf-8')
    issues = []

    for node in docstring_nodes(src):
        text = node.value
        first = text.strip().splitlines()[0] if text.strip() else ''
        if IMPERATIVE.match(first):
            issues.append(f'{path}:{node.lineno}  повелительное наклонение  "{first[:64]}"')

    tree_ok = True
    try:
        module = ast.parse(src)
    except SyntaxError:
        tree_ok = False
    if tree_ok and ast.get_docstring(module):
        issues.append(f'{path}:1  шапка модуля - по правилам убирается')

    pieces = [(node.lineno, node.value) for node in docstring_nodes(src)]
    pieces += [(line, text) for line, _, text in comment_spans(src)]
    for line_no, text in pieces:
        for offset, raw in enumerate(text.splitlines()):
            here = line_no + offset
            if ';' in raw:
                issues.append(f'{path}:{here}  точка с запятой  "{raw.strip()[:64]}"')
            if prose_colon(raw):
                issues.append(f'{path}:{here}  двоеточие прозой  "{raw.strip()[:64]}"')
            bad = sorted({ch for ch in raw if ch in AWKWARD})
            if bad:
                names = ', '.join(
                    f'{ch!r} ({unicodedata.name(ch, "?")})' if ch != " "
                    else 'неразрывный пробел' for ch in bad
                )
                issues.append(f'{path}:{here}  символы: {names}')
    return issues


def main() -> int:
    """Печатает найденные нарушения и отдаёт код возврата."""
    files = targets(sys.argv[1:])
    if not files:
        print('нечего проверять')
        return 0
    total = 0
    for path in files:
        found = report(path)
        if found:
            print(f'\n--- {path}')
            for line in found:
                print(f'  {line}')
            total += len(found)
    print(f'\nвсего нарушений: {total} в {len(files)} файлах')
    return 1 if total else 0


if __name__ == '__main__':
    raise SystemExit(main())
