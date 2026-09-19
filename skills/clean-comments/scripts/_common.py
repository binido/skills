"""Общая часть скриптов: где искать комментарии и докстринги."""

from __future__ import annotations

import ast
import io
import subprocess
import sys
import tokenize
from pathlib import Path

SKIP_PARTS = {'.venv', 'venv', '__pycache__', 'migrations', 'node_modules', '.git'}


def changed_files(base: str = 'develop') -> list[Path]:
    """Отдаёт изменённые в ветке .py файлы относительно базы."""
    try:
        merge_base = subprocess.run(
            ['git', 'merge-base', 'HEAD', base],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        names = subprocess.run(
            ['git', 'diff', '--name-only', f'{merge_base}..HEAD'],
            capture_output=True, text=True, check=True,
        ).stdout.split()
    except subprocess.CalledProcessError:
        print(f'не найдена база "{base}", укажите ветку аргументом', file=sys.stderr)
        return []
    return [Path(n) for n in names if n.endswith('.py') and usable(Path(n))]


def usable(path: Path) -> bool:
    """Проверяет, что файл существует и не лежит в служебном каталоге."""
    return path.is_file() and not SKIP_PARTS.intersection(path.parts)


def targets(argv: list[str]) -> list[Path]:
    """Отдаёт файлы из аргументов, а если их нет - изменённые в ветке."""
    args = [a for a in argv if not a.startswith('-')]
    explicit = [Path(a) for a in args if a.endswith('.py')]
    if explicit:
        return [p for p in explicit if usable(p)]
    base = next((a for a in args if not a.endswith('.py')), 'develop')
    return changed_files(base)


def comment_spans(src: str) -> list[tuple[int, int, str]]:
    """Отдаёт (строка, колонка, текст) для каждого комментария."""
    spans = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                spans.append((tok.start[0], tok.start[1], tok.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return spans


def docstring_nodes(src: str) -> list[ast.Constant]:
    """Отдаёт узлы-докстринги модуля, классов и функций."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef,
                                 ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, 'body', [])
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            found.append(body[0].value)
    return found
