import os
import random
from datetime import datetime
import requests

# 1. Настройки
USERNAME = "Thesavewill"
TOKEN = os.getenv("GITHUB_TOKEN", "")

# Твой ручной стек технологий
MY_STACK = [
    ("Python", "#3572A5"),
    ("Git", "#F05032"),
    ("Docker", "#2496ED"),
    ("Linux", "#FCC624"),
    ("VS Code", "#007ACC"),
]

# Цвета для автоматического парсинга языков GitHub
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Java": "#b07219",
    "Shell": "#89e051",
}

# ==========================================
# ПАРСИНГ ДАННЫХ С GITHUB API
# ==========================================
def fetch_github_data(username, token=""):
    """Собирает всю информацию о профиле и языках за один проход."""
    headers = {"Authorization": f"token {token}"} if token else {}

    try:
        user_resp = requests.get(
            f"https://api.github.com/users/{username}", headers=headers, timeout=5
        )
        repos_resp = requests.get(
            f"https://api.github.com/users/{username}/repos?per_page=100",
            headers=headers,
            timeout=5,
        )
    except Exception:
        user_resp = repos_resp = None

    if not user_resp or user_resp.status_code != 200 or repos_resp.status_code != 200:
        print("Лимит API или нет сети. Используются тестовые данные.")
        return {
            "username": username,
            "repos_count": 12,
            "followers": 5,
            "following": 8,
            "stars": 24,
            "created_year": 2022,
            "top_langs": [("Python", 72.5), ("HTML", 18.0), ("CSS", 9.5)],
        }

    user_data = user_resp.json()
    repos_data = repos_resp.json()

    total_stars = 0
    lang_bytes = {}

    for repo in repos_data:
        if repo.get("fork"):
            continue
        total_stars += repo.get("stargazers_count", 0)

        lang = repo.get("language")
        size = repo.get("size", 1)
        if lang:
            lang_bytes[lang] = lang_bytes.get(lang, 0) + size

    total_size = sum(lang_bytes.values()) or 1
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:3]
    top_langs = [
        (lang, round((size / total_size) * 100, 1))
        for lang, size in sorted_langs
    ]

    if not top_langs:
        top_langs = [("Нет кода", 100.0)]

    created_at = user_data.get("created_at", "2020-01-01")
    created_year = int(created_at[:4])

    return {
        "username": user_data.get("login", username),
        "repos_count": user_data.get("public_repos", 0),
        "followers": user_data.get("followers", 0),
        "following": user_data.get("following", 0),
        "stars": total_stars,
        "created_year": created_year,
        "top_langs": top_langs,
    }


# ==========================================
# КОСМИЧЕСКИЙ ФОН (ЗВЁЗДЫ-СЮРИКЕНЫ И КОМЕТЫ)
# ==========================================
def shuriken_path(size):
    """Генерирует SVG-путь 4-конечной звезды-сюрикена с центром в (0, 0)."""
    s = size          # Длина острых лучей
    c = size * 0.32   # Внутренний изгиб между лучами
    return (
        f"M 0,{-s} "
        f"Q {c},{-c} {s},0 "
        f"Q {c},{c} 0,{s} "
        f"Q {-c},{c} {-s},0 "
        f"Q {-c},{-c} 0,{-s} Z"
    )


def space_background():
    """Генерирует мерцающие звезды-сюрикены и кометы с длинным шлейфом."""
    random.seed(42)
    stars_svg = ""
    star_colors = ["#ffffff", "#e0f2fe", "#c7d2fe", "#fae8ff"]

    for _ in range(42):
        cx = random.randint(15, 585)
        cy = random.randint(15, 385)
        size = random.choice([2.5, 3.5, 4.5, 6.0])
        color = random.choice(star_colors)
        delay = round(random.uniform(0, 4), 2)
        dur = round(random.uniform(2.2, 4.8), 2)
        path_d = shuriken_path(size)

        # Внешний <g> держит координату (cx, cy), а внутренний <path> крутится и мерцает вокруг (0,0)
        stars_svg += f"""
        <g transform="translate({cx}, {cy})">
            <path d="{path_d}" fill="{color}" class="star" style="animation-delay: {delay}s; animation-duration: {dur}s;"/>
        </g>"""

    # Настройки комет: (start_x, start_y, задержка, длительность, масштаб)
    comets_data = [
        (220, -40, 0.3, 4.2, 1.0),
        (420, -40, 1.8, 3.6, 0.85),
        (620, -20, 0.9, 4.8, 1.15),
        (660, 120, 2.7, 3.9, 0.9),
        (520, -40, 4.1, 3.5, 1.0),
    ]
    comets_svg = ""
    head_shuriken = shuriken_path(4.5)

    for cx, cy, delay, dur, scale in comets_data:
        comets_svg += f"""
        <g transform="translate({cx}, {cy}) rotate(-35) scale({scale})">
            <g class="comet" style="animation-delay: {delay}s; animation-duration: {dur}s;">
                <!-- Внешний широкий мягкий шлейф кометы -->
                <polygon points="0,-3.5 160,0 0,3.5" fill="url(#comet-trail)" opacity="0.55"/>
                <!-- Яркое внутреннее ядро шлейфа -->
                <polygon points="0,-1.4 95,0 0,1.4" fill="url(#comet-core)"/>
                <!-- Голова кометы в виде светящегося сюрикена -->
                <path d="{head_shuriken}" fill="#ffffff" filter="url(#glow)"/>
            </g>
        </g>"""

    return f"""
    <g clip-path="url(#card-clip)">
        <rect width="600" height="400" fill="url(#space-grad)"/>
        {stars_svg}
        {comets_svg}
    </g>
    """


# ==========================================
# МОДУЛИ КАРТОЧКИ
# ==========================================
def empty_module(x, y):
    """Пустой прозрачный модуль-заглушка для резервирования слота под большой модуль."""
    return f"""<g transform="translate({x}, {y})">
        <rect width="150" height="100" x="0" y="0" fill="none" stroke="none"/>
    </g>"""

def wide_profile_module(x, y):
    """Пример БОЛЬШОГО модуля на 2 слота (ширина: 150 + 35 + 150 = 335)."""
    years = datetime.now().year - DATA["created_year"]
    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="335" height="100" x="0" y="0" rx="12" class="mod-bg" stroke="#58a6ff" stroke-width="1.5"/>
            <circle cx="315" cy="20" r="4" class="pulse-dot"/>
            <text x="20" y="28" class="mod-title">ПРОФИЛЬ</text>
            <text x="20" y="60" class="mod-value-lg" fill="#ffffff">@{DATA['username']}</text>
            <text x="20" y="84" class="mod-sub">На GitHub с {DATA['created_year']} года ({years} y.)</text>
        </g>
    </g>"""


def profile_module(x, y):
    """Стандартный модуль профиля (150x100)."""
    years = datetime.now().year - DATA["created_year"]
    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="150" height="100" x="0" y="0" rx="12" class="mod-bg" stroke="#30363d" stroke-width="1.5"/>
            <circle cx="130" cy="20" r="4" class="pulse-dot"/>
            <text x="15" y="25" class="mod-title">ПРОФИЛЬ</text>
            <text x="15" y="60" class="mod-value-md">@{DATA['username']}</text>
            <text x="15" y="80" class="mod-sub">С {DATA['created_year']} ({years} г.)</text>
        </g>
    </g>"""


def repos_module(x, y):
    """Модуль 2: Количество репозиториев."""
    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="150" height="100" x="0" y="0" rx="12" class="mod-bg" stroke="#58a6ff" stroke-width="1.5"/>
            <text x="15" y="25" class="mod-title">РЕПОЗИТОРИИ</text>
            <text x="15" y="60" class="mod-value-lg" fill="#58a6ff">{DATA['repos_count']}</text>
            <text x="15" y="85" class="mod-sub">Публичных проектов</text>
        </g>
    </g>"""


def stars_module(x, y):
    """Модуль 3: Количество звезд."""
    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="150" height="100" x="0" y="0" rx="12" class="mod-bg" stroke="#e3b341" stroke-width="1.5"/>
            <text x="15" y="25" class="mod-title">STARS</text>
            <text x="15" y="60" class="mod-value-lg" fill="#e3b341">★ {DATA['stars']}</text>
            <text x="15" y="85" class="mod-sub">Всего получено</text>
        </g>
    </g>"""


def followers_module(x, y):
    """Модуль 4: Подписчики и подписки."""
    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="150" height="100" x="0" y="0" rx="12" class="mod-bg" stroke="#3fb950" stroke-width="1.5"/>
            <text x="15" y="25" class="mod-title">СООБЩЕСТВА</text>
            <text x="15" y="60" class="mod-value-lg" fill="#3fb950">{DATA['followers']}</text>
            <text x="15" y="85" class="mod-sub">Подписок: {DATA['following']}</text>
        </g>
    </g>"""


def top_langs_module(x, y):
    """Модуль 5: Авто-статистика языков с GitHub."""
    bars = ""
    for idx, (lang, pct) in enumerate(DATA["top_langs"]):
        bar_y = 38 + idx * 20
        bar_w = max(int((pct / 100) * 120), 4)
        color = LANG_COLORS.get(lang, "#8b949e")
        bars += f"""
        <text x="15" y="{bar_y}" class="lang-text">{lang}</text>
        <text x="135" y="{bar_y}" class="lang-pct" text-anchor="end">{pct}%</text>
        <rect x="15" y="{bar_y + 3}" width="120" height="5" rx="2.5" fill="#21262d" fill-opacity="0.8"/>
        <rect x="15" y="{bar_y + 3}" width="{bar_w}" height="5" rx="2.5" fill="{color}" class="bar-anim"/>
        """

    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="150" height="230" x="0" y="0" rx="12" class="mod-bg" stroke="#a371f7" stroke-width="1.5"/>
            <text x="15" y="22" class="mod-title">ТОП ЯЗЫКОВ</text>
            {bars}
        </g>
    </g>"""


def stack_module(x, y):
    """Модуль 6: Выставление своего стека (плашки-бейджи 2x3)."""
    badges = ""
    for idx, (tech, color) in enumerate(MY_STACK[:6]):
        col = idx % 2
        row = idx // 2
        bx = 12 + col * 66
        by = 32 + row * 21
        badges += f"""
        <g transform="translate({bx}, {by})">
            <rect x="0" y="0" width="60" height="16" rx="4" fill="#21262d" fill-opacity="0.75" stroke="{color}" stroke-width="1"/>
            <text x="30" y="11.5" class="badge-text" text-anchor="middle">{tech}</text>
        </g>"""

    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="150" height="100" x="0" y="0" rx="12" class="mod-bg" stroke="#f78166" stroke-width="1.5"/>
            <text x="15" y="22" class="mod-title">МОЙ СТЕК</text>
            {badges}
        </g>
    </g>"""


# ==========================================
# ДВИЖОК СЕТКИ
# ==========================================
def modularity(columns, use_modules):
    """Расположение модулей на SVG-карточке по столбцам."""
    widths = [
        int(m(0, 0).split('width="')[1].split('"')[0]) for m in use_modules
    ]
    heights = [
        int(m(0, 0).split('height="')[1].split('"')[0]) for m in use_modules
    ]
    base_width = min(widths)
    base_height = min(heights)

    free_space = 600 - base_width * columns
    padding = free_space // (columns + 1)

    startX = padding
    startY = 25

    stepX = base_width + padding
    stepY = base_height + 25

    result_svg = ""

    for i in range(len(use_modules)):
        column = i % columns
        row = i // columns

        x = startX + column * stepX
        y = startY + row * stepY

        mod_svg = use_modules[i](x, y)
        delay = round(i * 0.1, 2)
        mod_svg = mod_svg.replace(
            'class="module"',
            f'class="module" style="animation-delay: {delay}s"',
        )

        result_svg += mod_svg + "\n"

    return result_svg


def generate_svg(username):
    """Собирает SVG-файл с космическим фоном и CSS-анимацией."""
    svg_template = f"""<svg width="1000" height="500" viewBox="0 0 1000 500" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <!-- Обрезка фона по скругленным краям карточки -->
        <clipPath id="card-clip">
            <rect width="600" height="400" rx="12"/>
        </clipPath>

        <!-- Глубокий космический градиент -->
        <linearGradient id="space-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#04060a"/>
            <stop offset="50%" stop-color="#0a101d"/>
            <stop offset="100%" stop-color="#140c29"/>
        </linearGradient>

        <!-- Внешний градиент шлейфа кометы -->
        <linearGradient id="comet-trail" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#58a6ff" stop-opacity="0.95"/>
            <stop offset="40%" stop-color="#a371f7" stop-opacity="0.45"/>
            <stop offset="100%" stop-color="#150d2a" stop-opacity="0"/>
        </linearGradient>

        <!-- Яркий внутренний градиент шлейфа -->
        <linearGradient id="comet-core" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>
            <stop offset="50%" stop-color="#79c0ff" stop-opacity="0.6"/>
            <stop offset="100%" stop-color="#58a6ff" stop-opacity="0"/>
        </linearGradient>

        <!-- Свечение головы кометы -->
        <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="2.2" result="blur"/>
            <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    </defs>

    <style>
        .mod-title {{ font: 700 10px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; letter-spacing: 0.8px; }}
        .mod-value-lg {{ font: 700 26px 'Segoe UI', Ubuntu, Sans-Serif; }}
        .mod-value-md {{ font: 700 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}
        .mod-sub {{ font: 400 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
        
        .lang-text {{ font: 600 10px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}
        .lang-pct {{ font: 400 9px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
        .badge-text {{ font: 600 9px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}

        /* Полупрозрачный фон модулей */
        .mod-bg {{
            fill: #161b22;
            fill-opacity: 0.62;
        }}

        /* Плавное появление модулей на СВОИХ местах снизу вверх */
        .module {{
            opacity: 0;
            animation: slideUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }}

        .bar-anim {{
            transform: scaleX(0);
            transform-origin: 15px center;
            animation: grow 1.2s ease-out forwards;
        }}

        .pulse-dot {{
            fill: #3fb950;
            animation: pulse 2s infinite;
        }}

        /* Анимация мерцания сюрикенов строго вокруг своего центра (0, 0) */
        .star {{
            animation: twinkle infinite ease-in-out;
        }}

        /* Анимация полета кометы со шлейфом */
        .comet {{
            opacity: 0;
            animation: shoot infinite ease-in;
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(18px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes grow {{
            from {{ transform: scaleX(0); }}
            to {{ transform: scaleX(1); }}
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.2; }}
        }}

        @keyframes twinkle {{
            0%, 100% {{ opacity: 0.25; transform: scale(0.65) rotate(0deg); }}
            50% {{ opacity: 1; transform: scale(1.25) rotate(20deg); }}
        }}

        @keyframes shoot {{
            0% {{ transform: translateX(0); opacity: 0; }}
            8% {{ opacity: 1; }}
            75% {{ opacity: 1; }}
            100% {{ transform: translateX(-750px); opacity: 0; }}
        }}
    </style>

    <!-- 1. Космический фон со звездами-сюрикенами и кометами -->
    {space_background()}

    <!-- 2. Сетка модулей -->
    {modularity(columns, use_modules)}

    <!-- 3. Внешняя рамка карточки поверх фона -->
    <rect width="598" height="398" x="1" y="1" rx="12" fill="none" stroke="#30363d" stroke-width="1.5"/>
</svg>"""

    with open("stats.svg", "w", encoding="utf-8") as f:
        f.write(svg_template)
    print("Карточка успешно сохранена в файл stats.svg!")


# ==========================================
# ЗАПУСК И НАСТРОЙКА СЕТКИ
# ==========================================
columns = 3

use_modules = [
    wide_profile_module,
    empty_module,
    repos_module,
    stars_module,
    followers_module,
    top_langs_module,
    stack_module,
]

if __name__ == "__main__":
    DATA = fetch_github_data(USERNAME, TOKEN)
    generate_svg(USERNAME)
