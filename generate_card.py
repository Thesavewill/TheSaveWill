import os
import random
import re
from datetime import datetime

import requests

# 1. Settings
USERNAME = "Thesavewill"
TOKEN = os.getenv("GITHUB_TOKEN", "")

# Card dimensions (840px width, 575px height for header + 3 rows)
CARD_WIDTH = 840
CARD_HEIGHT = 575

# Manual tech stack
MY_STACK = [
    ("Python", "#3572A5"),
    ("Git", "#F05032"),
    ("Docker", "#2496ED"),
    ("Linux", "#FCC624"),
    ("VS Code", "#007ACC"),
]

# Manual Pinned repositories (leave empty [] for automatic parsing)
# Format: [("repo-name", "Python", 5), ("another-repo", "HTML", 2)]
MY_PINNED = []

# GitHub language colors
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Kotlin": "#A97BFF",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Java": "#b07219",
    "Shell": "#89e051",
}


# ==========================================
# GITHUB API DATA FETCHING
# ==========================================
def fetch_contributions(username, token=""):
    """Fetches total contributions for the last year."""
    if token:
        query = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar {
                totalContributions
              }
            }
          }
        }
        """
        try:
            resp = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": {"login": username}},
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                return (
                    data["data"]["user"]["contributionsCollection"][
                        "contributionCalendar"
                    ]["totalContributions"]
                )
        except Exception:
            pass

    # Fallback without token via public contributions API
    try:
        resp = requests.get(
            f"https://github-contributions-api.jogruber.de/v4/{username}?y=last",
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("total", {}).get("lastYear", 195)
    except Exception:
        pass

    return 195


def fetch_pinned_repos(username, repos_data, token=""):
    """Fetches pinned repositories or top-2 repositories."""
    if MY_PINNED:
        return MY_PINNED[:2]

    # 1. Via GraphQL (if token is provided)
    if token:
        query = """
        query($login: String!) {
          user(login: $login) {
            pinnedItems(first: 2, types: REPOSITORY) {
              nodes {
                ... on Repository {
                  name
                  stargazerCount
                  primaryLanguage {
                    name
                  }
                }
              }
            }
          }
        }
        """
        try:
            resp = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": {"login": username}},
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            if resp.status_code == 200:
                nodes = (
                    resp.json()
                    .get("data", {})
                    .get("user", {})
                    .get("pinnedItems", {})
                    .get("nodes", [])
                )
                if nodes:
                    return [
                        (
                            n["name"],
                            (n.get("primaryLanguage") or {}).get("name") or "Code",
                            n.get("stargazerCount", 0),
                        )
                        for n in nodes
                    ]
        except Exception:
            pass

    # 2. Parse pinned repositories from profile page (without token)
    try:
        page = requests.get(f"https://github.com/{username}", timeout=5)
        if page.status_code == 200:
            pinned_names = re.findall(
                r'<span class="repo" title="([^"]+)">', page.text
            )
            if pinned_names and repos_data:
                repo_map = {r["name"]: r for r in repos_data if isinstance(r, dict)}
                pinned_list = []
                for name in pinned_names[:2]:
                    r = repo_map.get(name, {})
                    pinned_list.append(
                        (
                            name,
                            r.get("language") or "Code",
                            r.get("stargazers_count", 0),
                        )
                    )
                if pinned_list:
                    return pinned_list
    except Exception:
        pass

    # 3. Fallback: top-2 repositories by stars and update date
    if repos_data:
        own_repos = [r for r in repos_data if not r.get("fork")]
        own_repos.sort(
            key=lambda x: (x.get("stargazers_count", 0), x.get("updated_at", "")),
            reverse=True,
        )
        if own_repos:
            return [
                (
                    r["name"],
                    r.get("language") or "Code",
                    r.get("stargazers_count", 0),
                )
                for r in own_repos[:2]
            ]

    return [("Plotter", "Kotlin", 2), ("TheSaveWill", "Python", 0)]


def fetch_github_data(username, token=""):
    """Collects profile info, languages, contributions, and pinned repos."""
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

    contributions = fetch_contributions(username, token)

    if not user_resp or user_resp.status_code != 200 or repos_resp.status_code != 200:
        print("API rate limit or offline. Using fallback data.")
        return {
            "username": username,
            "repos_count": 5,
            "stars": 2,
            "created_year": 2025,
            "top_langs": [("HTML", 92.0), ("Kotlin", 4.4), ("Python", 3.7)],
            "contributions": contributions,
            "pinned": fetch_pinned_repos(username, [], token),
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
        top_langs = [("No code", 100.0)]

    created_at = user_data.get("created_at", "2025-01-01")
    created_year = int(created_at[:4])

    return {
        "username": user_data.get("login", username),
        "repos_count": user_data.get("public_repos", 0),
        "stars": total_stars,
        "created_year": created_year,
        "top_langs": top_langs,
        "contributions": contributions,
        "pinned": fetch_pinned_repos(username, repos_data, token),
    }


# ==========================================
# SPACE BACKGROUND (SHURIKEN STARS & COMETS)
# ==========================================
def shuriken_path(size):
    """Generates SVG path of a 4-pointed shuriken star centered at (0, 0)."""
    s = size
    c = size * 0.32
    return (
        f"M 0,{-s} "
        f"Q {c},{-c} {s},0 "
        f"Q {c},{c} 0,{s} "
        f"Q {-c},{c} {-s},0 "
        f"Q {-c},{-c} 0,{-s} Z"
    )


def space_background():
    """Generates twinkling shuriken stars and shooting comets across the card."""
    random.seed(42)
    stars_svg = ""
    star_colors = ["#ffffff", "#e0f2fe", "#c7d2fe", "#fae8ff"]

    for _ in range(110):
        cx = random.randint(15, CARD_WIDTH - 15)
        cy = random.randint(15, CARD_HEIGHT - 15)
        size = random.choice([2.5, 3.5, 4.5, 6.0])
        color = random.choice(star_colors)
        delay = round(random.uniform(0, 4), 2)
        dur = round(random.uniform(2.2, 4.8), 2)
        path_d = shuriken_path(size)

        stars_svg += f"""
        <g transform="translate({cx}, {cy})">
            <path d="{path_d}" fill="{color}" class="star" style="animation-delay: {delay}s; animation-duration: {dur}s;"/>
        </g>"""

    comets_data = [
        (350, -40, 0.3, 4.2, 1.0),
        (650, -40, 1.8, 3.6, 0.85),
        (880, 40, 0.9, 4.8, 1.15),
        (900, 220, 2.7, 3.9, 0.9),
        (880, 380, 4.1, 3.5, 1.0),
        (750, -40, 5.2, 4.4, 0.95),
    ]
    comets_svg = ""
    head_shuriken = shuriken_path(4.5)

    for cx, cy, delay, dur, scale in comets_data:
        comets_svg += f"""
        <g transform="translate({cx}, {cy}) rotate(-35) scale({scale})">
            <g class="comet" style="animation-delay: {delay}s; animation-duration: {dur}s;">
                <polygon points="0,-3.5 160,0 0,3.5" fill="url(#comet-trail)" opacity="0.55"/>
                <polygon points="0,-1.4 95,0 0,1.4" fill="url(#comet-core)"/>
                <path d="{head_shuriken}" fill="#ffffff" filter="url(#glow)"/>
            </g>
        </g>"""

    return f"""
    <g clip-path="url(#card-clip)">
        <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" fill="url(#space-grad)"/>
        {stars_svg}
        {comets_svg}
    </g>
    """


# ==========================================
# CARD MODULES (NARROW LEFT & WIDE RIGHT)
# ==========================================
LEFT_W = 190   # Narrow left column width
RIGHT_W = 388  # Stretched right column width
WIDE_W = 428   # Top centered profile width
MOD_H = 110


def wide_profile_module(x, y):
    """Top centered profile module."""
    years = max(1, datetime.now().year - DATA["created_year"])
    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="{WIDE_W}" height="{MOD_H}" x="0" y="0" rx="12" class="mod-bg" stroke="#58a6ff" stroke-width="1.5"/>
            <circle cx="{WIDE_W - 22}" cy="22" r="4.5" class="pulse-dot"/>
            <text x="22" y="30" class="mod-title">PROFILE</text>
            <text x="22" y="65" class="mod-value-lg" fill="#ffffff">@{DATA['username']}</text>
            <text x="22" y="90" class="mod-sub">On GitHub since {DATA['created_year']} ({years} y.)</text>
        </g>
    </g>"""


def repos_module(x, y):
    """Left Column 1: Public repositories count."""
    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="{LEFT_W}" height="{MOD_H}" x="0" y="0" rx="12" class="mod-bg" stroke="#58a6ff" stroke-width="1.5"/>
            <text x="16" y="28" class="mod-title">REPOSITORIES</text>
            <text x="16" y="66" class="mod-value-lg" fill="#58a6ff">{DATA['repos_count']}</text>
            <text x="16" y="92" class="mod-sub">Public projects</text>
        </g>
    </g>"""


def stars_module(x, y):
    """Left Column 2: Total stars count."""
    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="{LEFT_W}" height="{MOD_H}" x="0" y="0" rx="12" class="mod-bg" stroke="#e3b341" stroke-width="1.5"/>
            <text x="16" y="28" class="mod-title">STARS</text>
            <text x="16" y="66" class="mod-value-lg" fill="#e3b341">★ {DATA['stars']}</text>
            <text x="16" y="92" class="mod-sub">Total earned</text>
        </g>
    </g>"""


def contributions_module(x, y):
    """Left Column 3: Contributions in the last year."""
    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="{LEFT_W}" height="{MOD_H}" x="0" y="0" rx="12" class="mod-bg" stroke="#39d353" stroke-width="1.5"/>
            <text x="16" y="28" class="mod-title">ACTIVITY</text>
            <text x="16" y="66" class="mod-value-lg" fill="#39d353">{DATA['contributions']}</text>
            <text x="16" y="92" class="mod-sub">Contributions last year</text>
        </g>
    </g>"""


def top_langs_module(x, y):
    """Right Column 1: Stretched top languages module (borderless)."""
    bars = ""
    bar_max_w = RIGHT_W - 40
    for idx, (lang, pct) in enumerate(DATA["top_langs"]):
        bar_y = 40 + idx * 23
        bar_w = max(int((pct / 100) * bar_max_w), 4)
        color = LANG_COLORS.get(lang, "#8b949e")
        bars += f"""
        <text x="20" y="{bar_y}" class="lang-text">{lang}</text>
        <text x="{RIGHT_W - 20}" y="{bar_y}" class="lang-pct" text-anchor="end">{pct}%</text>
        <rect x="20" y="{bar_y + 4}" width="{bar_max_w}" height="5" rx="2.5" fill="#21262d" fill-opacity="0.8"/>
        <rect x="20" y="{bar_y + 4}" width="{bar_w}" height="5" rx="2.5" fill="{color}" class="bar-anim"/>
        """

    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="{RIGHT_W}" height="{MOD_H}" x="0" y="0" rx="12" class="mod-bg" stroke="none"/>
            <text x="20" y="22" class="mod-title">TOP LANGUAGES</text>
            {bars}
        </g>
    </g>"""


def stack_module(x, y):
    """Right Column 2: Stretched tech stack module (borderless)."""
    badges = ""
    badge_w = (RIGHT_W - 52) // 2  # 168px per badge
    for idx, (tech, color) in enumerate(MY_STACK[:6]):
        col = idx % 2
        row = idx // 2
        bx = 20 + col * (badge_w + 12)
        by = 34 + row * 23
        badges += f"""
        <g transform="translate({bx}, {by})">
            <rect x="0" y="0" width="{badge_w}" height="18" rx="4" fill="#21262d" fill-opacity="0.75" stroke="{color}" stroke-width="1"/>
            <text x="{badge_w / 2}" y="12.5" class="badge-text" text-anchor="middle">{tech}</text>
        </g>"""

    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="{RIGHT_W}" height="{MOD_H}" x="0" y="0" rx="12" class="mod-bg" stroke="none"/>
            <text x="20" y="23" class="mod-title">MY STACK</text>
            {badges}
        </g>
    </g>"""


def pinned_module(x, y):
    """Right Column 3: Stretched pinned repositories module (borderless)."""
    items_svg = ""
    card_w = RIGHT_W - 40
    for idx, (name, lang, stars) in enumerate(DATA["pinned"][:2]):
        py = 33 + idx * 34
        color = LANG_COLORS.get(lang, "#8b949e")
        short_name = name if len(name) <= 32 else name[:30] + "…"
        items_svg += f"""
        <g transform="translate(20, {py})">
            <rect width="{card_w}" height="28" rx="6" fill="#21262d" fill-opacity="0.75" stroke="#30363d" stroke-width="1"/>
            <circle cx="14" cy="14" r="4" fill="{color}"/>
            <text x="26" y="17.5" class="lang-text">{short_name}</text>
            <text x="{card_w - 12}" y="17.5" class="lang-pct" fill="#e3b341" text-anchor="end">★ {stars}</text>
        </g>"""

    return f"""<g transform="translate({x}, {y})">
        <g class="module">
            <rect width="{RIGHT_W}" height="{MOD_H}" x="0" y="0" rx="12" class="mod-bg" stroke="none"/>
            <text x="20" y="23" class="mod-title">PINNED</text>
            {items_svg}
        </g>
    </g>"""


# ==========================================
# LAYOUT ENGINE
# ==========================================
def modularity(header_module, grid_modules):
    """Positions the centered header and asymmetric left/right columns."""
    result_svg = ""

    # 1. Top centered PROFILE module
    header_x = (CARD_WIDTH - WIDE_W) // 2  # 206px
    header_y = 25
    header_svg = header_module(header_x, header_y).replace(
        'class="module"', 'class="module" style="animation-delay: 0.0s"'
    )
    result_svg += header_svg + "\n"

    # 2. Asymmetric columns: left moved rightwards (x=80) and wide right (x=436)
    left_x = 110
    right_x = CARD_WIDTH - 32 - RIGHT_W  # 436px
    start_y = 165
    step_y = MOD_H + 25  # 135px vertical step

    for i, mod_func in enumerate(grid_modules):
        col = i % 2
        row = i // 2

        x = left_x if col == 0 else right_x
        y = start_y + row * step_y

        mod_svg = mod_func(x, y)
        delay = round((i + 1) * 0.1, 2)
        mod_svg = mod_svg.replace(
            'class="module"',
            f'class="module" style="animation-delay: {delay}s"',
        )
        result_svg += mod_svg + "\n"

    return result_svg


def generate_svg(username):
    """Builds the final SVG file with space background and CSS animations."""
    svg_template = f"""<svg width="100%" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <clipPath id="card-clip">
            <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="12"/>
        </clipPath>

        <linearGradient id="space-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#04060a"/>
            <stop offset="50%" stop-color="#0a101d"/>
            <stop offset="100%" stop-color="#140c29"/>
        </linearGradient>

        <linearGradient id="comet-trail" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#58a6ff" stop-opacity="0.95"/>
            <stop offset="40%" stop-color="#a371f7" stop-opacity="0.45"/>
            <stop offset="100%" stop-color="#150d2a" stop-opacity="0"/>
        </linearGradient>

        <linearGradient id="comet-core" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>
            <stop offset="50%" stop-color="#79c0ff" stop-opacity="0.6"/>
            <stop offset="100%" stop-color="#58a6ff" stop-opacity="0"/>
        </linearGradient>

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
        .mod-value-lg {{ font: 700 28px 'Segoe UI', Ubuntu, Sans-Serif; }}
        .mod-value-md {{ font: 700 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}
        .mod-sub {{ font: 400 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
        
        .lang-text {{ font: 600 10.5px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}
        .lang-pct {{ font: 400 9.5px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
        .badge-text {{ font: 600 9.5px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}

        .mod-bg {{
            fill: #161b22;
            fill-opacity: 0.62;
        }}

        .module {{
            opacity: 0;
            animation: slideUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }}

        .bar-anim {{
            transform: scaleX(0);
            transform-origin: 20px center;
            animation: grow 1.2s ease-out forwards;
        }}

        .pulse-dot {{
            fill: #3fb950;
            animation: pulse 2s infinite;
        }}

        .star {{
            animation: twinkle infinite ease-in-out;
        }}

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
            100% {{ transform: translateX(-1100px); opacity: 0; }}
        }}
    </style>

    <!-- 1. Space background -->
    {space_background()}

    <!-- 2. Modules grid -->
    {modularity(header_module, grid_modules)}

    <!-- 3. Outer card border -->
    <rect width="{CARD_WIDTH - 2}" height="{CARD_HEIGHT - 2}" x="1" y="1" rx="12" fill="none" stroke="#30363d" stroke-width="1.5"/>
</svg>"""

    with open("stats.svg", "w", encoding="utf-8") as f:
        f.write(svg_template)
    print("Card successfully saved to stats.svg!")


# ==========================================
# RUN & CONFIGURE GRID
# ==========================================
header_module = wide_profile_module

# 3 rows x 2 columns (Narrow Left, Stretched Borderless Right)
grid_modules = [
    repos_module,          # Row 1, Left
    top_langs_module,      # Row 1, Right
    stars_module,          # Row 2, Left
    stack_module,          # Row 2, Right
    contributions_module,  # Row 3, Left
    pinned_module,         # Row 3, Right
]

if __name__ == "__main__":
    DATA = fetch_github_data(USERNAME, TOKEN)
    generate_svg(USERNAME)