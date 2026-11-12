# skills

Мои скилы для AI-агентов.

## Установка

**Claude Code** (плагин):

```
/plugin marketplace add binido/skills
/plugin install binido-skills@binido
```

Скилы вызываются как `/binido-skills:<имя>`. Обновить: `/plugin marketplace update binido`, либо включить автообновление в `/plugin` → Marketplaces.

**Другие агенты** (Codex, Cursor, Gemini CLI и др.):

```bash
npx skills@latest add binido/skills -g
```

Установщик спросит, какие скилы ставить и в какие агенты. Claude Code в списке сними: для него есть плагин, иначе скилы задвоятся. Обновлять той же командой, а не `npx skills update`: update ставит скилы во все найденные на машине агенты, включая Claude Code.

## Скилы

| Скил | Что делает |
|------|------------|
| [branch-desc](skills/branch-desc/SKILL.md) | Описание изменений ветки для MR/PR |
| [change](skills/change/SKILL.md) | Общий процесс нетривиального изменения, дополняющий профильные скиллы любого агента |
| [clean-comments](skills/clean-comments/SKILL.md) | Чистка уже написанных комментариев и докстрингов |
| [comment-style](skills/comment-style/SKILL.md) | Сразу пишет комментарии и докстринги в нужном стиле |
| [mentor](skills/mentor/SKILL.md) | Режим наставника: подсказки вместо готового кода, только ручной вызов |
| [verify-endpoint](skills/verify-endpoint/SKILL.md) | Проверка HTTP-ручек на локальном сервере |

## Как добавить скил

1. Создать `skills/<имя>/SKILL.md` с frontmatter `name` (совпадает с именем папки) и `description`.
2. Скрипты и доп. файлы класть рядом, в папку скила.
3. Закоммитить и запушить. Версия плагина берётся из коммита, поэтому поднимать её руками не нужно.
