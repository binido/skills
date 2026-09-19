"""
Самопроверка скриптов скилла на синтетическом файле.

Запускать после любой правки списков символов или логики разбора. Обе ошибки, которые
здесь ловятся, уже случались - молча портили код, а не падали.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import normalize_chars  # noqa: E402
import scan_comments  # noqa: E402

SAMPLE = '''"""Шапка — с тире и «ёлочками»."""

MESSAGE = 'Ошибка «доступ закрыт» — текст для пользователя'
ARROW = '→'


def build(value: int) -> str:
    """Собрать строку; вернуть результат: вот так."""
    # Комментарий с — тире, «ёлочками», стрелкой → и 5 ≤ 10
    return f'{MESSAGE}{ARROW}{value}'
'''


def check_code_strings_untouched() -> None:
    """Символы в строковых литералах - данные, трогать их нельзя."""
    fixed, _ = normalize_chars.rewrite(SAMPLE)
    assert "'Ошибка «доступ закрыт» — текст для пользователя'" in fixed, (
        'замена залезла в строковый литерал кода'
    )
    assert "ARROW = '→'" in fixed, 'замена испортила литерал со стрелкой'


def check_comments_normalised() -> None:
    """В комментариях и докстрингах заменяется всё, а не первая пара символов."""
    fixed, count = normalize_chars.rewrite(SAMPLE)
    comment = next(line for line in fixed.splitlines() if line.strip().startswith('#'))
    assert '—' not in comment and '«' not in comment, 'тире или ёлочки остались'
    assert '->' in comment and '<=' in comment, 'стрелка или знак сравнения не заменены'
    assert fixed.splitlines()[0] == '"""Шапка - с тире и "ёлочками"."""', 'шапка не вычищена'
    assert count >= 8, f'заменено подозрительно мало символов - {count}'


def check_ascii_not_flagged() -> None:
    """Обычные кавычки и апостроф неудобными не считаются."""
    assert '"' not in scan_comments.AWKWARD, 'ASCII-кавычка попала в список неудобных'
    assert "'" not in scan_comments.AWKWARD, 'ASCII-апостроф попал в список неудобных'


def check_scanner_finds_issues() -> None:
    """Сканер видит шапку, точку с запятой, двоеточие прозой и символы."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'probe.py'
        path.write_text(SAMPLE, encoding='utf-8')
        found = ' '.join(scan_comments.report(path))
    for expected in ('шапка модуля', 'точка с запятой', 'двоеточие прозой',
                     'повелительное наклонение', 'символы:'):
        assert expected in found, f'сканер не нашёл: {expected}'


def main() -> int:
    """Прогоняет все проверки."""
    checks = [
        check_code_strings_untouched,
        check_comments_normalised,
        check_ascii_not_flagged,
        check_scanner_finds_issues,
    ]
    for check in checks:
        check()
        print(f'ok  {check.__name__}')
    print(f'\nвсе проверки пройдены ({len(checks)})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
