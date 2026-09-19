"""
Меняет неудобные символы на простые аналоги внутри комментариев и докстрингов.

Строковые литералы кода не трогаются - там символы могут быть данными, а не текстом для
разработчика. Именно поэтому нужен разбор кода, а не sed по файлу.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import comment_spans, docstring_nodes, targets  # noqa: E402

# Что не набирается с обычной клавиатуры и на что это меняется.
# Буква ё, знак № и градус °, наоборот, остаются: первые два есть на русской раскладке,
# а у градуса нет короткого аналога.
REPLACEMENTS = {
    '\u2014': '-',      # длинное тире
    '\u2013': '-',      # среднее тире
    '\u00ab': '"',      # открывающая ёлочка
    '\u00bb': '"',      # закрывающая ёлочка
    '\u201c': '"',      # открывающая кавычка-запятая
    '\u201d': '"',      # закрывающая кавычка-запятая
    '\u2018': "'",      # открывающий апостроф
    '\u2019': "'",      # закрывающий апостроф
    '\u2026': '...',    # многоточие
    '\u2192': '->',
    '\u2190': '<-',
    '\u2194': '<->',
    '\u2264': '<=',
    '\u2265': '>=',
    '\u2260': '!=',
    '\u00b2': '2',
    '\u00b3': '3',
    '\u20bd': 'руб.',
    '\u00a0': ' ',      # неразрывный пробел
}


def swap(text: str) -> str:
    """Заменяет неудобные символы в куске текста."""
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def regions(src: str) -> list[tuple[int, int]]:
    """
    Отдаёт (начало, конец) в символах для каждого комментария и докстринга.

    ast считает колонки в байтах UTF-8, а tokenize - в символах. На кириллице это
    расходится вдвое, поэтому колонки узлов ast переводятся в символы отдельно.
    """
    lines = src.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))

    def from_chars(row: int, col: int) -> int:
        return starts[row - 1] + col

    def from_bytes(row: int, byte_col: int) -> int:
        line = lines[row - 1]
        prefix = line.encode('utf-8')[:byte_col].decode('utf-8', errors='ignore')
        return starts[row - 1] + len(prefix)

    spans = []
    for row, col, text in comment_spans(src):
        begin = from_chars(row, col)
        spans.append((begin, begin + len(text)))
    for node in docstring_nodes(src):
        if node.end_lineno is None or node.end_col_offset is None:
            continue
        spans.append((
            from_bytes(node.lineno, node.col_offset),
            from_bytes(node.end_lineno, node.end_col_offset),
        ))
    return sorted(spans)


def rewrite(src: str) -> tuple[str, int]:
    """Отдаёт новый текст файла и число заменённых символов."""
    spans = regions(src)
    out, cursor, changed = [], 0, 0
    for begin, end in spans:
        if begin < cursor:
            continue
        out.append(src[cursor:begin])
        piece = src[begin:end]
        fixed = swap(piece)
        changed += sum(1 for ch in piece if ch in REPLACEMENTS)
        out.append(fixed)
        cursor = end
    out.append(src[cursor:])
    return ''.join(out), changed


def main() -> int:
    """Показывает или применяет замены."""
    write = '--write' in sys.argv
    files = targets([a for a in sys.argv[1:] if a != '--write'])
    if not files:
        print('нечего проверять')
        return 0
    total = 0
    for path in files:
        src = path.read_text(encoding='utf-8')
        fixed, changed = rewrite(src)
        if not changed:
            continue
        total += changed
        print(f'{path}: {changed} символов')
        if write:
            path.write_text(fixed, encoding='utf-8')
    if not total:
        print('неудобных символов не найдено')
    elif write:
        print(f'\nзаменено {total} символов, проверьте линтер и тесты')
    else:
        print(f'\nнайдено {total} символов, запустите с --write чтобы заменить')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
