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
                     f'<text x="400" y="{y}" class="val" text-anchor="end">{val}</text>')

    lang_svg = ""
    colors = ["#FFFFFF", "#D6F3FF", "#B6F07A", "#FFE9A8"]
    for i, (name, pct) in enumerate(d["langs"]):
        y = 112 + i * 38
        w = max(4, int(300 * pct / 100))
        lang_svg += (f'<text x="494" y="{y}" class="lbl">{html.escape(name)}</text>'
                     f'<text x="838" y="{y}" class="val" text-anchor="end">{pct:.0f}%</text>'
                     f'<rect x="494" y="{y + 8}" width="344" height="9" rx="4.5" fill="#FFFFFF" opacity="0.25"/>'
                     f'<rect x="494" y="{y + 8}" width="{w * 344 // 300}" height="9" rx="4.5" '
                     f'fill="{colors[i % 4]}"/>')
    if not d["langs"]:
        lang_svg = '<text x="494" y="118" class="lbl">sem dados ainda</text>'

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
  <clipPath id="all"><rect width="900" height="320" rx="18"/></clipPath>
</defs>
<g clip-path="url(#all)">
  <rect width="900" height="320" fill="url(#sky)"/>
  <path d="M0 270 Q160 225 340 255 T680 248 T900 228 L900 320 L0 320Z" fill="url(#h1)"/>
  {background()}
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
    {stat_svg}
    <text x="494" y="72" class="ttl">Linguagens</text>
    {lang_svg}
  </g>
  <g stroke="#FFFFFF" stroke-opacity=".75" stroke-width="1.5">
    <circle class="bub" cx="18" cy="290" r="16" fill="url(#bub)"/>
    <circle class="bub" cx="450" cy="296" r="11" fill="url(#bub)"/>
    <circle class="bub" cx="884" cy="288" r="15" fill="url(#bub)"/>
    <circle class="bub" cx="884" cy="22" r="9" fill="url(#bub)"/>
  </g>
</g>
</svg>
'''


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(collect()), encoding="utf-8")
    print("ok:", OUT)
