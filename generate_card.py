import os
import requests

# 1. Настройки
USERNAME = "Thesavewill"
# Токен не обязателен для публичных репо, но с ним выше лимиты запросов
TOKEN = os.getenv("GITHUB_TOKEN", "")

# Палитра цветов для популярных языков
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "C++": "#f34b7d",
    "Java": "#b07219",
    "Shell": "#89e051",
}

def get_language_stats(username, token=""):
    """Парсит языки программирования по всем публичным репозиториям."""
    headers = {"Authorization": f"token {token}"} if token else {}
    
    # Получаем список репозиториев пользователя
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    repos = requests.get(repos_url, headers=headers).json()

    if not isinstance(repos, list):
        print("Ошибка при получении данных:", repos)
        return [("Python", 75.0), ("HTML", 25.0)]  # Тестовые данные, если лимит исчерпан

    lang_bytes = {}
    for repo in repos:
        # Пропускаем форки, чтобы считать только свой код
        if repo.get("fork"):
            continue
        
        # Запрашиваем языки конкретного репозитория (возвращает количество байт кода)
        langs_data = requests.get(repo["languages_url"], headers=headers).json()
        if isinstance(langs_data, dict):
            for lang, count in langs_data.items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + count

    total_bytes = sum(lang_bytes.values())
    if total_bytes == 0:
        return [("Нет данных", 100.0)]

    # Переводим байты в проценты и берем ТОП-4 языка
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:4]
    return [(lang, round((count / total_bytes) * 100, 1)) for lang, count in sorted_langs]


def generate_svg(username, stats):
    """Собирает SVG-файл с CSS-анимацией."""
    bars_svg = ""
    start_y = 75          # Начальная координата Y для первого языка
    max_bar_width = 260   # Максимальная ширина полоски прогресса (в пикселях)

    # Генерируем блок для каждого языка в цикле
    for i, (lang, percent) in enumerate(stats):
        y = start_y + i * 42
        bar_width = max((percent / 100) * max_bar_width, 4)  # Минимум 4px, чтобы полоску было видно
        color = LANG_COLORS.get(lang, "#8b949e")
        delay = i * 0.2  # Задержка анимации для каждого следующего ряда

        bars_svg += f"""
        <g class="row" style="animation-delay: {delay}s">
            <!-- Название языка и процент -->
            <text x="25" y="{y}" class="lang-name">{lang}</text>
            <text x="375" y="{y}" class="lang-percent" text-anchor="end">{percent}%</text>
            
            <!-- Серый фон прогресс-бара -->
            <rect x="25" y="{y + 8}" width="{max_bar_width}" height="8" rx="4" fill="#21262d" />
            
            <!-- Цветная анимированная полоска -->
            <rect x="25" y="{y + 8}" width="{bar_width}" height="8" rx="4" fill="{color}" 
                  class="progress-bar" style="animation-delay: {delay + 0.2}s" />
        </g>
        """

    # Основной шаблон SVG
    svg_template = f"""<svg width="400" height="255" viewBox="0 0 400 255" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style>
        /* Стили текста */
        .title {{ font: 600 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: #58a6ff; }}
        .lang-name {{ font: 600 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}
        .lang-percent {{ font: 400 12px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}

        /* Анимация плавного появления строк */
        .row {{
            opacity: 0;
            animation: fadeIn 0.6s ease-out forwards;
        }}

        /* Анимация заполнения шкалы слева направо */
        .progress-bar {{
            transform: scaleX(0);
            transform-origin: 25px center;
            animation: growBar 1s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }}

        /* Пульсирующий индикатор в углу */
        .pulse-dot {{
            fill: #3fb950;
            animation: pulse 2s infinite;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes growBar {{
            from {{ transform: scaleX(0); }}
            to {{ transform: scaleX(1); }}
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}
    </style>

    <!-- Темный фон карточки с рамкой -->
    <rect width="398" height="253" x="1" y="1" rx="12" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>

    <!-- Шапка карточки -->
    <circle cx="370" cy="32" r="5" class="pulse-dot" />
    <text x="25" y="37" class="title">Топ языков @{username}</text>
    <line x1="25" y1="50" x2="375" y2="50" stroke="#21262d" stroke-width="1"/>

    <!-- Вставляем сгенерированные полоски языков -->
    {bars_svg}
</svg>"""

    with open("stats.svg", "w", encoding="utf-8") as f:
        f.write(svg_template)
    print("Карточка успешно сохранена в файл stats.svg!")


if __name__ == "__main__":
    stats_data = get_language_stats(USERNAME, TOKEN)
    generate_svg(USERNAME, stats_data)