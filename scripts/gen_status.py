"""Gera assets/status.svg com dados reais do GitHub (estilo Frutiger Aero).

Uso:  python scripts/gen_status.py
Env:  GH_USER (padrão ctf090), GITHUB_TOKEN (opcional, necessário para commits),
      DEMO=1 usa números de exemplo, sem acessar a rede.
Foto de fundo (opcional): assets/fundo.jpg (ou .png)
"""
import base64
import html
import json
import os
import urllib.request
from pathlib import Path

USER = os.environ.get("GH_USER", "ctf090")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = Path("assets/status.svg")


def api(url, data=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "status-svg"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def collect():
    if os.environ.get("DEMO"):
        return {"repos": 3, "stars": 1, "followers": 0, "commits": 13,
                "langs": [("C++", 78.0), ("Python", 14.0), ("Shell", 8.0)]}

    user = api(f"https://api.github.com/users/{USER}")
    repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    stars = sum(r["stargazers_count"] for r in repos)

    totals = {}
    for r in repos:
        if r["fork"]:
            continue
        try:
            for lang, n in api(r["languages_url"]).items():
                totals[lang] = totals.get(lang, 0) + n
        except Exception:
            pass
    soma = sum(totals.values()) or 1
    langs = sorted(((k, v * 100 / soma) for k, v in totals.items()),
                   key=lambda x: -x[1])[:4]

    commits = None
    if TOKEN:
        try:
            q = ('{ user(login: "%s") { contributionsCollection '
                 '{ totalCommitContributions } } }' % USER)
            res = api("https://api.github.com/graphql",
                      json.dumps({"query": q}).encode())
            commits = res["data"]["user"]["contributionsCollection"]["totalCommitContributions"]
        except Exception:
            commits = None

    return {"repos": user["public_repos"], "stars": stars,
            "followers": user["followers"], "commits": commits, "langs": langs}


def background():
    for name in ("assets/fundo.jpg", "assets/fundo.jpeg", "assets/fundo.png"):
        p = Path(name)
        if p.exists():
            mime = "image/png" if p.suffix == ".png" else "image/jpeg"
            b64 = base64.b64encode(p.read_bytes()).decode()
            return (f'<image href="data:{mime};base64,{b64}" x="0" y="0" '
                    f'width="900" height="320" preserveAspectRatio="xMidYMid slice"/>'
                    f'<rect width="900" height="320" fill="#0A4F85" opacity="0.18"/>')
    return ""


def build(d):
    rows = [("Repositórios", d["repos"]), ("Estrelas", d["stars"]),
            ("Seguidores", d["followers"])]
    if d["commits"] is not None:
        rows.append(("Commits (último ano)", d["commits"]))

    stat_svg = ""
    for i, (label, val) in enumerate(rows):
        y = 118 + i * 34
        stat_svg += (f'<text x="62" y="{y}" class="lbl">{html.escape(label)}</text>'
                     f'<text x="400" y="{y}" class="val" text-anchor="end">{val}</text>'
                     f'<line x1="62" y1="{y + 11}" x2="400" y2="{y + 11}" stroke="#FFFFFF" stroke-opacity=".2"/>')

    lang_svg = ""
    colors = ["#FFFFFF", "#D6F3FF", "#B6F07A", "#FFE9A8"]
    for i, (name, pct) in enumerate(d["langs"]):
        y = 112 + i * 38
        w = max(4, int(300 * pct / 100))
        lang_svg += (f'<text x="494" y="{y}" class="lbl">{html.escape(name)}</text>'
                     f'<text x="838" y="{y}" class="val" text-anchor="end">{pct:.0f}%</text>'
                     f'<rect x="494" y="{y + 8}" width="344" height="9" rx="4.5" fill="#FFFFFF" opacity="0.25"/>'
                     f'<rect class="grow" style="animation-delay:{i * 0.25}s" x="494" y="{y + 8}" width="{w * 344 // 300}" height="9" rx="4.5" '
                     f'fill="{colors[i % 4]}"/>'
                     f'<rect class="grow" style="animation-delay:{i * 0.25}s" x="496" y="{y + 9.5}" width="{max(2, w * 344 // 300 - 4)}" height="2.5" rx="1.25" fill="#FFFFFF" opacity=".55"/>')
    if not d["langs"]:
        lang_svg = '<text x="494" y="118" class="lbl">sem dados ainda</text>'

    import random
    rnd = random.Random(7)

    def bubble():
        x, y, r = rnd.uniform(10, 890), rnd.uniform(296, 316), rnd.uniform(3.5, 10)
        return (f'<g class="rise" style="animation-duration:{rnd.uniform(7, 13):.1f}s;animation-delay:-{rnd.uniform(0, 12):.1f}s">'
                f'<g class="wob" style="animation-duration:{rnd.uniform(2.5, 4.5):.1f}s">'
                f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="url(#bub)" stroke="#FFFFFF" stroke-opacity=".75" stroke-width="1.2"/>'
                f'<ellipse cx="{x - r * .35:.1f}" cy="{y - r * .45:.1f}" rx="{r * .3:.1f}" ry="{r * .16:.1f}" fill="#FFFFFF" opacity=".85"/>'
                f'</g></g>')

    def wave(y, amp):
        return f"M0 {y}q37.5 {-amp} 75 0" + " t75 0" * 23 + "V330H0Z"

    def blade(x, h, w, bend, fill):
        return (f'<path class="sway" style="animation-delay:-{rnd.random() * 4:.1f}s" '
                f'd="M{x - w:.1f} 322Q{x + bend * .3:.1f} {322 - h * .55:.1f} {x + bend:.1f} {322 - h:.1f}'
                f'Q{x + w + bend * .3:.1f} {322 - h * .5:.1f} {x + w:.1f} 322Z" fill="{fill}"/>')

    back_svg = (
        '<g style="mix-blend-mode:screen"><circle class="pulse" cx="870" cy="0" r="170" fill="url(#sunG)"/>'
        '<path class="tw" d="M870 14L875 36L897 41L875 46L870 68L865 46L843 41L865 36Z" fill="#FFFFFF" opacity=".9"/></g>'
        '<rect y="296" width="900" height="30" fill="url(#wg)"/>'
        f'<path class="w1" d="{wave(296, 5)}" fill="#FFFFFF" fill-opacity=".3"/>'
        f'<path class="w2" d="{wave(305, 4)}" fill="#0A64FF" fill-opacity=".3"/>'
        + "".join(bubble() for _ in range(22)))

    greens = ["#1F9A14", "#2FB31F", "#5FD020", "#8BE83A"]
    front_svg = "".join(
        blade(rnd.uniform(a, a + 150), rnd.uniform(28, 62), rnd.uniform(3, 5), rnd.uniform(-8, 8), rnd.choice(greens))
        for a in (0, 750) for _ in range(14))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 320" width="900" height="320">
<style>
  text {{ font-family: 'Segoe UI','Trebuchet MS',Verdana,sans-serif; fill: #FFFFFF; }}
  .ttl {{ font-size: 20px; font-weight: 700; }}
  .lbl {{ font-size: 15px; opacity: .95; }}
  .val {{ font-size: 17px; font-weight: 700; }}
  .bub {{ animation: float 7s ease-in-out infinite; }}
  .bub:nth-of-type(2n) {{ animation-duration: 9s; }}
  @keyframes float {{ 0%,100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-12px) }} }}
  .sweep {{ animation: sweep 6s ease-in-out infinite; }}
  @keyframes sweep {{ 0% {{ transform: translateX(-340px) }} 60%,100% {{ transform: translateX(360px) }} }}
  .rise {{ animation: rise linear infinite; }}
  @keyframes rise {{ 0% {{ transform: translateY(0); opacity: 0 }} 12% {{ opacity: 1 }} 88% {{ opacity: 1 }} 100% {{ transform: translateY(-250px); opacity: 0 }} }}
  .wob {{ animation: wob ease-in-out infinite alternate; }}
  @keyframes wob {{ from {{ transform: translateX(-6px) }} to {{ transform: translateX(6px) }} }}
  .sway {{ transform-box: fill-box; transform-origin: 50% 100%; animation: sway 4s ease-in-out infinite alternate; }}
  @keyframes sway {{ from {{ transform: rotate(-4deg) }} to {{ transform: rotate(4deg) }} }}
  .w1 {{ animation: wv 12s linear infinite; }}
  .w2 {{ animation: wv 18s linear infinite reverse; }}
  @keyframes wv {{ to {{ transform: translateX(-900px) }} }}
  .grow {{ transform-box: fill-box; transform-origin: left; animation: grow 1.6s cubic-bezier(.2,.8,.2,1) both; }}
  @keyframes grow {{ from {{ transform: scaleX(0) }} }}
  .pulse {{ transform-origin: 870px 0; animation: pulse 6s ease-in-out infinite; }}
  @keyframes pulse {{ 50% {{ transform: scale(1.08); opacity: .85 }} }}
  .tw {{ transform-box: fill-box; transform-origin: center; animation: tw 3s ease-in-out infinite; }}
  @keyframes tw {{ 50% {{ transform: scale(.55) rotate(45deg); opacity: .5 }} }}
</style>
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0D8BE8"/><stop offset=".6" stop-color="#5CC8F5"/><stop offset="1" stop-color="#C9F0FF"/>
  </linearGradient>
  <linearGradient id="h1" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#B6F07A"/><stop offset="1" stop-color="#3FA535"/>
  </linearGradient>
  <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#FFFFFF" stop-opacity=".45"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity=".18"/><stop offset="1" stop-color="#FFFFFF" stop-opacity=".1"/>
  </linearGradient>
  <linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#FFFFFF" stop-opacity=".55"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity=".35"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="bub" cx=".5" cy=".5" r=".5">
    <stop offset=".6" stop-color="#FFFFFF" stop-opacity=".05"/><stop offset="1" stop-color="#FFFFFF" stop-opacity=".55"/>
  </radialGradient>
  <filter id="sh" x="-10%" y="-10%" width="120%" height="140%">
    <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#0A5C99" flood-opacity=".45"/>
  </filter>
  <filter id="ts"><feDropShadow dx="0" dy="1.5" stdDeviation="1.5" flood-color="#0A4F85" flood-opacity=".6"/></filter>
  <clipPath id="c1"><rect x="30" y="30" width="400" height="250" rx="18"/></clipPath>
  <clipPath id="c2"><rect x="470" y="30" width="400" height="250" rx="18"/></clipPath>
  <radialGradient id="sunG">
    <stop offset="0" stop-color="#FFFFFF"/><stop offset=".25" stop-color="#FFFFFF"/><stop offset=".5" stop-color="#FFFBD0" stop-opacity=".5"/><stop offset="1" stop-color="#FFFBD0" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="wg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#5FE0FF" stop-opacity=".9"/><stop offset="1" stop-color="#0A6BFF" stop-opacity=".95"/>
  </linearGradient>
  <clipPath id="all"><rect width="900" height="320" rx="18"/></clipPath>
</defs>
<g clip-path="url(#all)">
  <rect width="900" height="320" fill="url(#sky)"/>
  <path d="M0 270 Q160 225 340 255 T680 248 T900 228 L900 320 L0 320Z" fill="url(#h1)"/>
  {background()}
  {back_svg}
  <g filter="url(#sh)">
    <rect x="30" y="30" width="400" height="250" rx="18" fill="url(#glass)" stroke="#FFFFFF" stroke-opacity=".8" stroke-width="1.5"/>
    <rect x="470" y="30" width="400" height="250" rx="18" fill="url(#glass)" stroke="#FFFFFF" stroke-opacity=".8" stroke-width="1.5"/>
  </g>
  <rect x="34" y="34" width="392" height="60" rx="14" fill="url(#gloss)"/>
  <rect x="474" y="34" width="392" height="60" rx="14" fill="url(#gloss)"/>
  <g clip-path="url(#c1)"><rect class="sweep" x="30" y="30" width="120" height="250" fill="url(#shine)" transform="skewX(-15)"/></g>
  <g clip-path="url(#c2)"><rect class="sweep" x="470" y="30" width="120" height="250" fill="url(#shine)" transform="skewX(-15)" style="animation-delay:1.5s"/></g>
  <g filter="url(#ts)">
    <text x="62" y="72" class="ttl">Status da conta</text>
    <line x1="62" y1="84" x2="400" y2="84" stroke="#FFFFFF" stroke-opacity=".45"/>
    {stat_svg}
    <text x="494" y="72" class="ttl">Linguagens</text>
    <line x1="494" y1="84" x2="838" y2="84" stroke="#FFFFFF" stroke-opacity=".45"/>
    {lang_svg}
  </g>
  <g stroke="#FFFFFF" stroke-opacity=".75" stroke-width="1.5">
    <circle class="bub" cx="18" cy="290" r="16" fill="url(#bub)"/>
    <circle class="bub" cx="450" cy="296" r="11" fill="url(#bub)"/>
    <circle class="bub" cx="884" cy="288" r="15" fill="url(#bub)"/>
    <circle class="bub" cx="884" cy="22" r="9" fill="url(#bub)"/>
  </g>
  {front_svg}
</g>
</svg>
'''


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(collect()), encoding="utf-8")
    print("ok:", OUT)
