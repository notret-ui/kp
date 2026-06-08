# Генератор КП «Печь.ру»

Инструмент для менеджеров: собрать красивое коммерческое предложение из товаров
pech.ru и выдать клиенту **веб-ссылку** + **PDF**. Визуал — по Figma-шаблону «КП-200825-ДАО».

- Концепция и структура: [`docs/superpowers/specs/2026-06-07-kp-generator-design.md`](docs/superpowers/specs/2026-06-07-kp-generator-design.md)
- Дизайн-система (бренд, токены, компоненты): [`docs/design-system.md`](docs/design-system.md)
- Референсы дизайна (Figma-экспорт): [`reference/`](reference/)

## Рабочий цикл

1. **Claude Code** — концепция, структура, дизайн-система (этот репозиторий).
2. **GitHub** — хранение, все обновления через коммиты.
3. **Claude design** — по дизайн-системе собирает прототип (HTML/CSS-мокапы всех слайдов)
   в [`prototype/`](prototype/). Сначала мокапы → апрув.
4. **Claude Code** — реализация в [`src/`](src/): данные (фид pech.ru, SQLite-поиск),
   FastAPI, Playwright→PDF подключаются к утверждённым мокапам.

## Стек

Python · FastAPI · Jinja2 · Playwright (headless Chromium для PDF) · SQLite (FTS5).

## Настройка окружения

Скопируй `.env.example` → `.env` и заполни. `.env` в гит не коммитится.
Секрет `APIFY_TOKEN` хранить только в `.env`.
