#!/usr/bin/env python3
"""Carrosséis v7 "mundos" (Impeccable) — Instagram 1080x1350 e TikTok 1080x1920.
Mesmo JSON do v6 + campo "look" no topo, que escolhe o MUNDO VISUAL do carrossel inteiro:
  impacto  — fundo escuro, manchete condensada gigante, virada em bloco de cor (o v6)
  caderno  — papel pautado, caneta azul, marca-texto e fita adesiva, traços feitos à mão
  recorte  — colagem: palavras em papéis recortados sobre a cor do pilar, fita, fotocópia
  tela     — interface de celular: notificação, notas, widget, campo de digitação
A identidade da conta (o @ e a cor do pilar) é a mesma em todos os mundos.
Uso: python3 render.py carrossel.json pasta_saida
Fontes: npm i @fontsource-variable/bricolage-grotesque @fontsource/kalam @fontsource/gloock  (FONT_DIR=<node_modules>)
Slides: cover{title,stat?,stat_label?,art?} story{text} big{text,tone?} reveal{number,text}
        versus{title,items,note?} chat{label?,messages,caption?} cta{lead,keyword,sub} follow{text com {handle}}
"""
import html, json, math, os, random, re, sys, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

PILLARS = {
    "ia": {"acc": "#4D7CFF", "dark": "#0B0F1E", "on": "#FFFFFF"},
    "comportamento": {"acc": "#FF4F8B", "dark": "#160A10", "on": "#FFFFFF"},
    "curiosidades": {"acc": "#FFB800", "dark": "#14110A", "on": "#121212"},
}
SIZES = {"instagram": (1080, 1350), "tiktok": (1080, 1920)}
LOOKS = ("impacto", "caderno", "recorte", "tela", "placar", "recibo", "quadrinho", "rotulo", "riso", "bauhaus",
         "pixel", "quadro", "mural", "tabloide", "telegrama")
GEN_LOOKS = LOOKS[4:]
LOOK_DIR = Path(__file__).resolve().parent / "looks"
YEL = "#FFE14D"
INK = "#121212"
PEN = "#1D3FE0"


def _lum(h):
    h = h.lstrip("#")
    c = [int(h[n:n + 2], 16) / 255 for n in (0, 2, 4)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def text_acc(acc, bg="#EDEDEA"):
    """cor do pilar escurecida até 4.5:1 sobre fundo claro (texto colorido legível)"""
    r, g, b = (int(acc[n:n + 2], 16) for n in (1, 3, 5))
    for k in range(0, 101, 4):
        f = 1 - k / 100
        hx = f"#{int(r * f):02X}{int(g * f):02X}{int(b * f):02X}"
        if (_lum(bg) + .05) / (_lum(hx) + .05) >= 4.5:
            return hx
    return INK


def typo(t):
    t = (t or "").replace("...", "…").replace("R$ ", "R$\u00a0")
    t = re.sub(r'"([^"]*)"', "“\\1”", t)
    t = re.sub(r"\b(em|de) (\d)", "\\1\u00a0\\2", t)
    return re.sub(r"(\d) (em|de|mil|milhões|bilhões|anos|dias|horas|vezes|pessoas)\b", "\\1\u00a0\\2", t)


def esc(t):
    return html.escape(typo(t))


def stars(t, cls):
    return re.sub(r"\*\*(.+?)\*\*", rf"<span class='{cls}'>\1</span>", esc(t)).replace("\n", "<br>")


def mark(t):
    return re.sub(r"==(.+?)==", r"<mark>\1</mark>", esc(t).replace("\n", "<br>"))


def plain(t):
    return re.sub(r"\*\*|==", "", t or "")


def paras(text):
    parts = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    return "".join(f"<p class='{'lead' if n == 0 else 'rest'}'>{mark(p)}</p>" for n, p in enumerate(parts))


# ---------------- traços à mão ----------------
def _path(pts):
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for a in range(1, len(pts) - 1):
        x1, y1 = pts[a]
        x2, y2 = pts[a + 1]
        d += f" Q{x1:.1f},{y1:.1f} {(x1 + x2) / 2:.1f},{(y1 + y2) / 2:.1f}"
    return d + f" L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"


def hand_circle(rnd, color, w=7):
    st = rnd.uniform(0, 6.28)
    pts = []
    for k in range(42):
        t = st + k / 41 * 6.28 * 1.12
        r = 1 + .05 * math.sin(t * 3)
        pts.append((50 + 48 * r * math.cos(t) + rnd.uniform(-1, 1), 50 + 45 * r * math.sin(t) + rnd.uniform(-1, 1)))
    return (f"<svg class='hc' viewBox='0 0 100 100' preserveAspectRatio='none'><path d='{_path(pts)}' fill='none' "
            f"stroke='{color}' vector-effect='non-scaling-stroke' style='stroke-width:{w}px' stroke-linecap='round'/></svg>")


def hand_under(rnd, color):
    pts = [(x, 55 + rnd.uniform(-9, 9)) for x in range(0, 101, 10)] + [(x, 78 + rnd.uniform(-8, 8)) for x in range(94, 20, -18)]
    return (f"<svg class='hu' viewBox='0 0 100 100' preserveAspectRatio='none'><path d='{_path(pts)}' fill='none' "
            f"stroke='{color}' vector-effect='non-scaling-stroke' style='stroke-width:6px' stroke-linecap='round'/></svg>")


def hand_arrow(rnd, color, w=190, h=110):
    pts = [(8, h * .3), (w * .35, h * .08 + rnd.uniform(-5, 5)), (w * .68, h * .4), (w - 16, h - 20)]
    ex, ey = pts[-1]
    return (f"<svg class='ha' width='{w}' height='{h}' viewBox='0 0 {w} {h}'><path d='{_path(pts)}' fill='none' "
            f"stroke='{color}' stroke-width='6' stroke-linecap='round'/><path d='M{ex - 34},{ey - 8} L{ex},{ey} "
            f"L{ex - 10},{ey - 34}' fill='none' stroke='{color}' stroke-width='6' stroke-linecap='round' stroke-linejoin='round'/></svg>")


def brush(rnd, color):
    top = [(x, 14 + rnd.uniform(-7, 7)) for x in range(-3, 104, 9)]
    bot = [(x, 90 + rnd.uniform(-7, 7)) for x in range(103, -4, -9)]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in top + bot) + " Z"
    return f"<svg class='brush' viewBox='0 0 100 100' preserveAspectRatio='none'><path d='{d}' fill='{color}'/></svg>"


def torn(rnd, n=16):
    """clip-path de papel rasgado (polygon em %)."""
    pts = []
    for k in range(n + 1):
        pts.append(f"{k * 100 / n:.1f}% {rnd.uniform(0, 3.5):.1f}%")
    for k in range(n + 1):
        pts.append(f"{100 - rnd.uniform(0, 2):.1f}% {k * 100 / n:.1f}%")
    for k in range(n, -1, -1):
        pts.append(f"{k * 100 / n:.1f}% {100 - rnd.uniform(0, 3.5):.1f}%")
    for k in range(n, -1, -1):
        pts.append(f"{rnd.uniform(0, 2):.1f}% {k * 100 / n:.1f}%")
    return "polygon(" + ",".join(pts) + ")"


SPOT = ("<svg class='spot' viewBox='0 0 1000 1000' preserveAspectRatio='none'><defs><linearGradient id='beam' x1='0' y1='0' "
        "x2='0' y2='1'><stop offset='0' stop-color='#fff' stop-opacity='.5'/><stop offset='1' stop-color='#fff' stop-opacity='0'/>"
        "</linearGradient></defs><polygon points='640,0 700,0 980,1000 380,1000' fill='url(#beam)'/>"
        "<rect x='625' y='0' width='90' height='16' rx='6' fill='#fff' fill-opacity='.9'/></svg>")

ARROW_SVG = ("<svg width='{s}' height='{s}' viewBox='0 0 44 44'><circle cx='22' cy='22' r='21' fill='{bg}'/>"
             "<path d='M13 22h17M24 15l7 7-7 7' stroke='{fg}' stroke-width='3.5' fill='none' stroke-linecap='round' "
             "stroke-linejoin='round'/></svg>")


# ---------------- CSS base (variáveis definidas por slide) ----------------
BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:var(--w);height:var(--h);overflow:hidden}
body{background:var(--bg);color:var(--fg);font-family:'Bric',sans-serif;position:relative;-webkit-font-smoothing:antialiased;
  font-optical-sizing:auto;font-kerning:normal}
.grain::before{content:'';position:absolute;inset:0;opacity:.09;pointer-events:none;z-index:50;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.75' numOctaves='3'/><feColorMatrix values='0 0 0 0 .5 0 0 0 0 .5 0 0 0 0 .5 0 0 0 .55 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")}
.wrap{position:absolute;inset:0;padding:var(--pt) var(--px) var(--pb);display:flex;flex-direction:column;justify-content:center;z-index:5}
.hd{position:absolute;left:var(--px);bottom:calc(var(--pb) - 92px);font:600 24px 'Bric';letter-spacing:.01em;color:var(--muted);z-index:20}
.prog{position:absolute;left:50%;transform:translateX(-50%);bottom:calc(var(--pb) - 86px);display:flex;gap:6px;z-index:20}
.prog i{display:block;width:24px;height:8px;border-radius:4px;background:var(--track)}
.prog i.on{background:var(--progc)}
.next{position:absolute;right:var(--px);bottom:calc(var(--pb) - 96px);font:800 26px 'Bric';letter-spacing:.08em;
  text-transform:uppercase;color:var(--fg);display:flex;align-items:center;gap:10px;z-index:20}
.next b{font-size:40px;line-height:1;color:var(--nextc)}
mark{background:linear-gradient(transparent 10%,#FFE14D 10%,#FFE14D 90%,transparent 90%);color:#121212;padding:0 .14em;
  box-decoration-break:clone}
.hc,.hu{position:absolute;pointer-events:none;overflow:visible}
.brush{position:absolute;left:-1%;top:4%;height:98%;z-index:0}
.cw>:first-child{margin-top:auto}
.grid{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:calc(18px*var(--s));max-width:100%}
.grid i{aspect-ratio:1;border-radius:50%;background:rgba(255,255,255,.16)}
.grid i.on{background:var(--acc)}
.hd.pill{background:#121212;color:#fff;padding:6px 16px;bottom:calc(var(--pb) - 100px)}
"""

# ---------- IMPACTO (v6) ----------
CSS_IMPACTO = """
.bloom{position:absolute;inset:0;background:radial-gradient(90% 60% at 100% 0%,color-mix(in srgb,var(--acc) 34%,transparent),transparent 70%),
  radial-gradient(70% 50% at 0% 100%,color-mix(in srgb,var(--acc) 14%,transparent),transparent 70%)}
.spot{position:absolute;inset:0;width:100%;height:100%;filter:blur(3px);opacity:.75}
.chandle{position:absolute;left:var(--px);top:calc(var(--pt) - 46px);font:700 calc(46px*var(--s)) 'Hand';color:#fff;transform:rotate(-5deg);
  transform-origin:left center;z-index:6}
.cwrap{position:absolute;left:calc(var(--px) - 12px);right:calc(var(--px) - 12px);top:calc(var(--pt) + 40px);bottom:calc(var(--pb) - 76px);
  display:flex;flex-direction:column;z-index:5}
.cwrap>:first-child{margin-top:auto}
.cstat{display:flex;align-items:flex-end;gap:22px;margin-bottom:calc(30px*var(--s))}
.cstat b{font-weight:800;font-stretch:75%;font-size:calc(250px*var(--s));line-height:.8;letter-spacing:-.03em;color:var(--acc)}
.cstat span{font:700 calc(36px*var(--s))/1.12 'Bric';color:#fff;opacity:.9;max-width:11ch;padding-bottom:8px}
h1{font-weight:800;font-stretch:75%;line-height:.98;letter-spacing:-.01em;color:#fff;text-wrap:balance}
.turn{background:linear-gradient(transparent 4%,var(--acc) 4%,var(--acc) 96%,transparent 96%);color:var(--on);padding:0 .1em;
  margin:0 -.03em;box-decoration-break:clone}
.swipe{display:flex;align-items:center;gap:18px;margin-top:calc(48px*var(--s));font:800 calc(30px*var(--s)) 'Bric';letter-spacing:.08em;
  text-transform:uppercase;color:#fff}
.swipe span{flex:1;height:3px;background:rgba(255,255,255,.3);border-radius:2px}
.lead{font-weight:800;font-stretch:94%;font-size:calc(82px*var(--s));line-height:1.02;letter-spacing:-.022em;text-wrap:pretty}
.rest{font-weight:560;font-size:calc(60px*var(--s));line-height:1.16;color:#262626;letter-spacing:-.02em;text-wrap:pretty}
p+p{margin-top:calc(46px*var(--s))}
.big p{font-weight:800;font-stretch:75%;line-height:.96;letter-spacing:-.015em;text-wrap:balance;color:var(--fg)}
.big .hi{color:var(--hl)}
.big.onacc .hi{color:#121212;background:linear-gradient(transparent 4%,var(--hl) 4%,var(--hl) 96%,transparent 96%);padding:0 .1em;
  box-decoration-break:clone}
.rnum{display:inline-block;align-self:flex-start;font-weight:800;font-stretch:75%;line-height:.82;letter-spacing:-.035em;color:var(--acc);white-space:nowrap}
.rtext{font-weight:780;font-stretch:94%;font-size:calc(84px*var(--s));line-height:1.02;letter-spacing:-.025em;margin-top:calc(40px*var(--s));color:#fff;text-wrap:balance}
.vtitle{font-weight:800;font-stretch:94%;font-size:calc(62px*var(--s));line-height:1.04;letter-spacing:-.024em;margin-bottom:calc(60px*var(--s));text-wrap:balance}
.vrow+.vrow{margin-top:calc(50px*var(--s))}
.vlab{font-weight:650;font-size:calc(38px*var(--s));color:#3a3a3a}
.vnum{font-weight:800;font-stretch:75%;font-size:calc(180px*var(--s));line-height:.9;letter-spacing:-.02em;margin-top:4px}
.vbar{height:calc(28px*var(--s));background:rgba(18,18,18,.09);border-radius:999px;margin-top:calc(16px*var(--s));overflow:hidden}
.vbar i{display:block;height:100%;border-radius:999px}
.vnote{font-weight:720;font-size:calc(54px*var(--s));line-height:1.12;letter-spacing:-.02em;margin-top:calc(60px*var(--s))}
.chat{gap:calc(24px*var(--s))}
.clab{align-self:flex-start;font:700 calc(26px*var(--s)) 'Bric';letter-spacing:.08em;text-transform:uppercase;color:#5a5a5a;
  border:2px solid rgba(18,18,18,.22);border-radius:999px;padding:8px 20px;margin-bottom:calc(14px*var(--s))}
.msg{display:flex;flex-direction:column;max-width:86%}
.msg.left{align-self:flex-start}.msg.right{align-self:flex-end;align-items:flex-end}
.msg small{font:650 calc(28px*var(--s)) 'Bric';color:#5a5a5a;margin:0 22px 8px}
.bub{font-weight:620;font-size:calc(56px*var(--s));line-height:1.18;letter-spacing:-.015em;padding:30px 38px;border-radius:42px;background:#fff;
  box-shadow:0 10px 24px -14px rgba(18,18,18,.35)}
.msg.left .bub{border-bottom-left-radius:12px}
.msg.right .bub{background:var(--acc);color:var(--on);border-bottom-right-radius:12px}
.ccap{font-weight:800;font-stretch:94%;font-size:calc(70px*var(--s));line-height:1.0;letter-spacing:-.026em;margin-top:calc(40px*var(--s));text-wrap:balance}
.clead{font-weight:740;font-size:calc(52px*var(--s));line-height:1.08;letter-spacing:-.02em;max-width:19ch;text-wrap:balance}
.comente{font-weight:800;font-stretch:75%;font-size:calc(270px*var(--s));line-height:.86;letter-spacing:-.02em;margin-top:calc(56px*var(--s))}
.kw{position:relative;display:block;margin-top:calc(10px*var(--s))}
.kw span{position:relative;z-index:1;display:inline-block;font-weight:800;font-stretch:75%;line-height:1;padding:0 18px;white-space:nowrap}
.sub{font-weight:640;font-size:calc(44px*var(--s));line-height:1.15;margin-top:calc(48px*var(--s));max-width:22ch;color:#262626}
.fol p{font-weight:800;font-stretch:80%;line-height:1;letter-spacing:-.02em;text-wrap:balance;color:#fff}
.fh{background:var(--acc);color:var(--on);padding:0 .12em;box-decoration-break:clone}
"""

# ---------- CADERNO ----------
CSS_CADERNO = """
body{background-color:#FBFAF5;
  background-image:linear-gradient(90deg,transparent calc(var(--px) - 26px),rgba(226,72,72,.55) calc(var(--px) - 26px),
    rgba(226,72,72,.55) calc(var(--px) - 23px),transparent calc(var(--px) - 23px)),
  repeating-linear-gradient(180deg,transparent 0,transparent 63px,rgba(29,63,224,.16) 63px,rgba(29,63,224,.16) 65px)}
.tape{position:absolute;width:230px;height:62px;background:color-mix(in srgb,var(--acc) 38%,rgba(255,255,255,.55));opacity:.85;z-index:8;
  box-shadow:0 2px 6px rgba(0,0,0,.08)}
.hand{font-family:'Hand';font-weight:700;color:#1D3FE0}
.hmk{position:relative;display:inline-block;white-space:nowrap}
.hmk>span{position:relative;z-index:1}
.hmk .hc{left:-8%;top:-14%;width:116%;height:128%;z-index:2}
.hmk .hu{left:-2%;bottom:-.3em;width:104%;height:.42em}
.cstat{display:flex;align-items:center;gap:30px;margin-bottom:calc(36px*var(--s))}
.cstat .hmk b{font:800 calc(210px*var(--s))/.9 'Bric';letter-spacing:-.04em;color:#121212;padding:0 .12em}
.cstat>span:last-child{font:700 calc(54px*var(--s))/1.05 'Hand';color:#1D3FE0;max-width:9ch;transform:rotate(-4deg)}
h1{font-weight:800;line-height:1.02;letter-spacing:-.02em;color:#121212;text-wrap:balance}
.turn{background:linear-gradient(transparent 52%,color-mix(in srgb,var(--acc) 70%,#fff) 52%,color-mix(in srgb,var(--acc) 70%,#fff) 92%,transparent 92%);
  box-decoration-break:clone}
.swipe{display:flex;align-items:flex-end;gap:8px;margin-top:calc(46px*var(--s));align-self:flex-end;font:700 calc(42px*var(--s)) 'Hand';color:#1D3FE0}
.swipe .ha{margin-bottom:-18px}
.chandle{position:absolute;right:var(--px);top:calc(var(--pt) - 40px);font:700 calc(40px*var(--s)) 'Hand';color:#1D3FE0;transform:rotate(3deg);z-index:9}
.lead{font-weight:780;font-size:calc(78px*var(--s));line-height:1.05;letter-spacing:-.022em;color:#121212;text-wrap:pretty}
.rest{font-weight:520;font-size:calc(56px*var(--s));line-height:1.22;color:#2a2a2a;text-wrap:pretty}
p+p{margin-top:calc(44px*var(--s))}
mark{background:linear-gradient(transparent 45%,color-mix(in srgb,var(--acc) 60%,#fff) 45%,color-mix(in srgb,var(--acc) 60%,#fff) 92%,transparent 92%)}
.big p{font-family:'Hand';font-weight:700;color:#1D3FE0;line-height:1.04;transform:rotate(-2deg);text-wrap:balance}
.big .hi{color:#121212;background:linear-gradient(transparent 50%,var(--acc) 50%,var(--acc) 90%,transparent 90%);
  box-decoration-break:clone}
.rnum{position:relative;display:inline-block;align-self:flex-start;font:800 1px/0.9 'Bric';letter-spacing:-.04em;color:#121212;white-space:nowrap;padding:0 .1em}
.rnum .hc{left:-10%;top:-16%;width:120%;height:132%}
.rtext{font:700 calc(64px*var(--s))/1.1 'Hand';color:#1D3FE0;margin-top:calc(50px*var(--s));transform:rotate(-2deg);text-wrap:balance}
.vtitle{font:700 calc(64px*var(--s))/1.05 'Hand';color:#1D3FE0;margin-bottom:calc(56px*var(--s));transform:rotate(-1.5deg)}
.vrow+.vrow{margin-top:calc(52px*var(--s))}
.vlab{font-weight:650;font-size:calc(40px*var(--s));color:#2a2a2a}
.vnum{font-weight:800;font-size:calc(160px*var(--s));line-height:.92;letter-spacing:-.03em;margin-top:6px}
.vbar{height:calc(44px*var(--s));margin-top:calc(12px*var(--s));border:4px solid #121212;border-radius:10px 14px 9px 12px;padding:5px;transform:rotate(-.6deg)}
.vbar i{display:block;height:100%;border-radius:6px;background-image:repeating-linear-gradient(-45deg,currentColor 0,currentColor 10px,transparent 10px,transparent 18px)}
.vnote{font-weight:720;font-size:calc(54px*var(--s));line-height:1.14;margin-top:calc(60px*var(--s))}
.chat{gap:calc(34px*var(--s))}
.clab{align-self:flex-start;font:700 calc(40px*var(--s)) 'Hand';color:#B32D2D;transform:rotate(-3deg);margin-bottom:calc(6px*var(--s))}
.msg{display:flex;flex-direction:column;max-width:84%}
.msg.left{align-self:flex-start;transform:rotate(-1.6deg)}.msg.right{align-self:flex-end;align-items:flex-end;transform:rotate(1.4deg)}
.msg small{font:700 calc(34px*var(--s)) 'Hand';color:#1D3FE0;margin:0 10px 6px}
.bub{font-weight:620;font-size:calc(54px*var(--s));line-height:1.2;padding:36px 40px 40px;background:#FFF3A6;color:#121212;
  box-shadow:0 14px 22px -16px rgba(0,0,0,.45)}
.msg.right .bub{background:color-mix(in srgb,var(--acc) 30%,#fff)}
.ccap{font:700 calc(66px*var(--s))/1.08 'Hand';color:#1D3FE0;margin-top:calc(30px*var(--s));transform:rotate(-1.5deg)}
.clead{font-weight:740;font-size:calc(54px*var(--s));line-height:1.1;max-width:19ch;text-wrap:balance}
.comente{font:700 calc(180px*var(--s))/1 'Hand';color:#1D3FE0;margin-top:calc(40px*var(--s));transform:rotate(-3deg);transform-origin:left}
.kw{position:relative;display:block;margin-top:calc(16px*var(--s))}
.kw .hmk span{font-weight:800;line-height:1;white-space:nowrap;color:#121212;padding:0 .15em}
.sub{font-weight:600;font-size:calc(46px*var(--s));line-height:1.15;margin-top:calc(54px*var(--s));max-width:22ch;color:#2a2a2a}
.fol p{font-weight:800;line-height:1.04;letter-spacing:-.02em;color:#121212;text-wrap:balance}
.fh{font-family:'Hand';color:#1D3FE0;white-space:nowrap}
.grid i{background:none;border:5px solid #1D3FE0}
.grid i.on{background:var(--acc);border-color:#121212}
.sig{font:700 calc(60px*var(--s)) 'Hand';color:#1D3FE0;margin-top:calc(50px*var(--s));transform:rotate(-4deg);transform-origin:left}
"""

# ---------- RECORTE ----------
CSS_RECORTE = """
body{background:var(--acc)}
.scrap{display:inline-block;padding:.06em .22em .1em;margin:.06em .06em;line-height:1;box-shadow:0 10px 18px -10px rgba(0,0,0,.45)}
.w-a{background:#fff;color:#121212;font-family:'Bric';font-weight:800;font-stretch:80%}
.w-b{background:#121212;color:#fff;font-family:'Gloock';font-weight:400}
.w-c{background:#FFE14D;color:#121212;font-family:'Bric';font-weight:800;font-stretch:92%}
.w-d{background:#F1EDE3;color:#121212;font-family:'Gloock';font-weight:400}
.w-t{background:#121212;color:var(--acc);font-family:'Bric';font-weight:800;font-stretch:78%}
.tape{position:absolute;width:200px;height:58px;background:rgba(255,255,255,.55);z-index:9;box-shadow:0 2px 6px rgba(0,0,0,.1)}
.cwrap{position:absolute;left:calc(var(--px) - 20px);right:calc(var(--px) - 20px);top:calc(var(--pt) + 10px);bottom:calc(var(--pb) - 70px);
  display:flex;flex-direction:column;z-index:5}
.cwrap>:first-child{margin-top:auto}
.title{line-height:1;text-wrap:balance;padding:0 8px}
.cstat{align-self:flex-start;display:flex;align-items:center;gap:22px;background:#121212;color:var(--acc);padding:26px 40px 30px;
  margin-bottom:calc(34px*var(--s));transform:rotate(-3deg)}
.cstat b{font:400 calc(190px*var(--s))/.85 'Gloock';letter-spacing:-.02em}
.cstat span{font:700 calc(36px*var(--s))/1.1 'Bric';color:#fff;max-width:10ch}
.chandle{position:absolute;left:var(--px);top:calc(var(--pt) - 52px);background:#121212;color:#fff;font:700 calc(32px*var(--s)) 'Bric';
  padding:8px 18px;transform:rotate(-2deg);z-index:9}
.swipe{align-self:flex-end;margin-top:calc(40px*var(--s));display:flex;align-items:center;gap:14px;background:#fff;color:#121212;
  font:800 calc(30px*var(--s)) 'Bric';letter-spacing:.08em;text-transform:uppercase;padding:14px 22px;transform:rotate(2deg)}
.card{position:relative;background:#FBF8F1;color:#121212;padding:calc(64px*var(--s)) calc(60px*var(--s));box-shadow:0 26px 40px -24px rgba(0,0,0,.55)}
.lead{font:400 calc(80px*var(--s))/1.04 'Gloock';letter-spacing:-.01em;text-wrap:pretty}
.rest{font-weight:560;font-size:calc(52px*var(--s));line-height:1.2;color:#2a2a2a;text-wrap:pretty}
p+p{margin-top:calc(40px*var(--s))}
.big .title{font-size:1px}
.rbox{align-self:flex-start;background:#121212;padding:20px 46px 34px;transform:rotate(-2.5deg);box-shadow:0 26px 40px -24px rgba(0,0,0,.6)}
.rnum{display:block;font:400 1px/.92 'Gloock';color:var(--acc);white-space:nowrap;letter-spacing:-.02em}
.rtext{align-self:flex-start;max-width:92%;margin-top:calc(44px*var(--s));background:#fff;color:#121212;font-weight:760;font-size:calc(58px*var(--s));
  line-height:1.1;padding:28px 34px;transform:rotate(1.5deg);box-shadow:0 18px 30px -20px rgba(0,0,0,.5);text-wrap:balance}
.vtitle{font:400 calc(64px*var(--s))/1.04 'Gloock';margin-bottom:calc(54px*var(--s))}
.vrow+.vrow{margin-top:calc(46px*var(--s))}
.vlab{font-weight:650;font-size:calc(38px*var(--s));color:#3a3a3a}
.vnum{font:400 calc(150px*var(--s))/.95 'Gloock';margin-top:6px}
.vbar{height:calc(46px*var(--s));margin-top:calc(12px*var(--s));background:#E8E2D4}
.vbar i{display:block;height:100%}
.vnote{font-weight:740;font-size:calc(50px*var(--s));line-height:1.14;margin-top:calc(52px*var(--s))}
.chat{gap:calc(30px*var(--s))}
.clab{align-self:flex-start;background:#121212;color:#fff;font:700 calc(26px*var(--s)) 'Bric';letter-spacing:.08em;text-transform:uppercase;padding:10px 20px;transform:rotate(-2deg)}
.msg{display:flex;flex-direction:column;max-width:86%}
.msg.left{align-self:flex-start;transform:rotate(-1.5deg)}.msg.right{align-self:flex-end;align-items:flex-end;transform:rotate(1.5deg)}
.msg small{font:800 calc(26px*var(--s)) 'Bric';letter-spacing:.06em;text-transform:uppercase;background:#121212;color:#fff;padding:6px 14px;margin-bottom:-6px;z-index:2;align-self:inherit}
.bub{font-weight:620;font-size:calc(54px*var(--s));line-height:1.18;padding:34px 40px;background:#fff;color:#121212;box-shadow:0 18px 30px -20px rgba(0,0,0,.5)}
.msg.right .bub{background:#FFE14D}
.ccap{align-self:flex-start;background:#121212;color:#fff;font:400 calc(64px*var(--s))/1.06 'Gloock';padding:18px 30px;margin-top:calc(26px*var(--s));transform:rotate(-1deg)}
.clead{align-self:flex-start;background:#fff;color:#121212;font-weight:760;font-size:calc(50px*var(--s));line-height:1.1;padding:22px 30px;max-width:92%;transform:rotate(-1.5deg)}
.comente{align-self:flex-start;background:#121212;color:#fff;font:400 calc(170px*var(--s))/1 'Gloock';padding:10px 36px 26px;margin-top:calc(40px*var(--s));transform:rotate(2deg)}
.kw{align-self:flex-start;margin-top:calc(18px*var(--s));background:#FFE14D;padding:4px 30px 14px;transform:rotate(-2deg);box-shadow:0 18px 30px -20px rgba(0,0,0,.5)}
.kw span{display:inline-block;font-weight:800;font-stretch:78%;line-height:1;white-space:nowrap;color:#121212}
.sub{align-self:flex-start;background:#fff;color:#121212;font-weight:640;font-size:calc(42px*var(--s));line-height:1.15;margin-top:calc(40px*var(--s));
  padding:16px 24px;max-width:90%;transform:rotate(1deg)}
.fol .title{font-size:1px}
.grid i{border-radius:0;background:#fff;box-shadow:0 8px 14px -8px rgba(0,0,0,.4)}
.grid i.on{background:#121212}
"""

# ---------- TELA ----------
CSS_TELA = """
body{background:radial-gradient(120% 70% at 50% 0%,color-mix(in srgb,var(--acc) 30%,#0B0C10),#0B0C10 70%);color:#fff}
.lock{position:absolute;left:0;right:0;top:calc(var(--pt) + 10px);text-align:center;z-index:4}
.lock b{display:block;font-weight:700;font-stretch:88%;font-size:calc(230px*var(--s));line-height:.9;letter-spacing:-.03em;color:#fff}
.lock span{display:block;font:600 calc(36px*var(--s)) 'Bric';color:rgba(255,255,255,.75);margin-top:10px}
.cwrap{position:absolute;left:calc(var(--px) - 20px);right:calc(var(--px) - 20px);top:calc(var(--pt) + 40px);bottom:calc(var(--pb) - 60px);
  display:flex;flex-direction:column;z-index:5}
.cwrap>:first-child{margin-top:auto}
.notif{background:rgba(255,255,255,.14);border-radius:46px;padding:34px 40px 40px;backdrop-filter:blur(30px);
  box-shadow:0 30px 60px -30px rgba(0,0,0,.6);border:1px solid rgba(255,255,255,.12)}
.nhead{display:flex;align-items:center;gap:18px;font:650 calc(30px*var(--s)) 'Bric';color:rgba(255,255,255,.8);margin-bottom:22px}
.app{width:calc(58px*var(--s));height:calc(58px*var(--s));border-radius:16px;background:var(--acc);display:grid;place-items:center;color:var(--on);
  font:800 calc(30px*var(--s)) 'Bric'}
.nhead em{margin-left:auto;font-style:normal;color:rgba(255,255,255,.55)}
h1{font-weight:780;line-height:1.04;letter-spacing:-.02em;color:#fff;text-wrap:balance}
.turn{color:var(--accl)}
.swipe{margin-top:calc(40px*var(--s));align-self:center;display:flex;flex-direction:column;align-items:center;gap:14px;font:650 calc(30px*var(--s)) 'Bric';color:rgba(255,255,255,.75)}
.swipe i{display:block;width:220px;height:10px;border-radius:5px;background:rgba(255,255,255,.85)}
.note{background:#F7F6F2;color:#121212;border-radius:44px;padding:calc(56px*var(--s)) calc(56px*var(--s));box-shadow:0 30px 60px -30px rgba(0,0,0,.7)}
.ntop{display:flex;justify-content:space-between;align-items:center;font:650 calc(28px*var(--s)) 'Bric';color:#626262;margin-bottom:calc(34px*var(--s))}
.ntop b{color:var(--acct);font-weight:750}
.lead{font-weight:780;font-size:calc(74px*var(--s));line-height:1.04;letter-spacing:-.022em;text-wrap:pretty}
.rest{font-weight:520;font-size:calc(52px*var(--s));line-height:1.22;color:#333;text-wrap:pretty}
p+p{margin-top:calc(38px*var(--s))}
.search{display:flex;align-items:center;gap:22px;background:rgba(255,255,255,.14);border-radius:999px;padding:26px 36px;margin-bottom:calc(60px*var(--s));
  font:600 calc(32px*var(--s)) 'Bric';color:rgba(255,255,255,.6)}
.search svg{flex:none}
.big p{font-weight:780;line-height:1.02;letter-spacing:-.025em;color:#fff;text-wrap:balance}
.big .hi{color:var(--accl)}
.caret{display:inline-block;width:.08em;height:.9em;background:var(--accl);vertical-align:-.08em;margin-left:.06em}
.widget{background:rgba(255,255,255,.12);border-radius:56px;padding:calc(60px*var(--s)) calc(56px*var(--s));border:1px solid rgba(255,255,255,.12)}
.wlab{font:650 calc(30px*var(--s)) 'Bric';color:rgba(255,255,255,.65);display:flex;align-items:center;gap:14px}
.wlab i{width:18px;height:18px;border-radius:50%;background:var(--accl)}
.rnum{display:inline-block;font-weight:750;font-stretch:86%;font-size:1px;line-height:.9;letter-spacing:-.035em;color:#fff;white-space:nowrap;margin-top:16px}
.rtext{font-weight:620;font-size:calc(54px*var(--s));line-height:1.16;color:rgba(255,255,255,.88);margin-top:calc(30px*var(--s));text-wrap:pretty}
.rtext mark{color:#121212}
.vpanel{background:#F7F6F2;color:#121212;border-radius:48px;padding:calc(56px*var(--s))}
.vtitle{font-weight:760;font-size:calc(54px*var(--s));line-height:1.08;letter-spacing:-.02em;margin-bottom:calc(48px*var(--s));text-wrap:balance}
.vrow+.vrow{margin-top:calc(40px*var(--s))}
.vlab{display:flex;justify-content:space-between;align-items:baseline;font-weight:620;font-size:calc(36px*var(--s));color:#444}
.vlab b{font-weight:780;font-size:calc(100px*var(--s));letter-spacing:-.03em;line-height:1}
.vbar{height:calc(34px*var(--s));background:#E3E1DB;border-radius:12px;margin-top:calc(14px*var(--s));overflow:hidden}
.vbar i{display:block;height:100%;border-radius:12px}
.vnote{font-weight:700;font-size:calc(46px*var(--s));line-height:1.14;margin-top:calc(46px*var(--s));color:#fff}
.chat{gap:calc(18px*var(--s))}
.ctop{display:flex;flex-direction:column;align-items:center;gap:10px;margin-bottom:calc(30px*var(--s))}
.ctop .app{width:calc(96px*var(--s));height:calc(96px*var(--s));border-radius:50%;font-size:calc(40px*var(--s))}
.ctop span{font:650 calc(30px*var(--s)) 'Bric';color:rgba(255,255,255,.8)}
.clab{align-self:center;font:600 calc(26px*var(--s)) 'Bric';color:rgba(255,255,255,.55);margin-bottom:10px}
.msg{display:flex;flex-direction:column;max-width:82%}
.msg.left{align-self:flex-start}.msg.right{align-self:flex-end;align-items:flex-end}
.msg small{font:600 calc(24px*var(--s)) 'Bric';color:rgba(255,255,255,.5);margin:0 18px 6px}
.bub{font-weight:520;font-size:calc(52px*var(--s));line-height:1.22;padding:26px 36px;border-radius:44px;background:#2A2B31;color:#fff}
.msg.left .bub{border-bottom-left-radius:14px}
.msg.right .bub{background:var(--acc);color:var(--on);border-bottom-right-radius:14px}
.ccap{font-weight:760;font-size:calc(62px*var(--s));line-height:1.04;letter-spacing:-.02em;margin-top:calc(40px*var(--s));color:#fff;text-wrap:balance}
.clead{font-weight:740;font-size:calc(58px*var(--s));line-height:1.08;letter-spacing:-.02em;color:#fff;max-width:18ch;text-wrap:balance}
.inputbar{display:flex;align-items:center;gap:22px;background:#F7F6F2;border-radius:999px;padding:22px 22px 22px 44px;margin-top:calc(60px*var(--s))}
.inputbar .typed{flex:1;font-weight:700;font-size:1px;line-height:1.1;color:#121212;white-space:nowrap;overflow:hidden}
.inputbar .send{flex:none;width:calc(96px*var(--s));height:calc(96px*var(--s));border-radius:50%;background:var(--acc);display:grid;place-items:center}
.sub{font-weight:600;font-size:calc(44px*var(--s));line-height:1.16;margin-top:calc(44px*var(--s));color:rgba(255,255,255,.8);max-width:22ch}
.kwlab{font:650 calc(30px*var(--s)) 'Bric';color:rgba(255,255,255,.6);margin-top:calc(60px*var(--s))}
.profile{display:flex;flex-direction:column;align-items:center;text-align:center}
.avatar{width:calc(220px*var(--s));height:calc(220px*var(--s));border-radius:50%;background:var(--acc);color:var(--on);display:grid;place-items:center;
  font:800 calc(90px*var(--s)) 'Bric';box-shadow:0 0 0 10px rgba(255,255,255,.12)}
.pname{font:780 calc(64px*var(--s)) 'Bric';margin-top:calc(34px*var(--s));letter-spacing:-.02em}
.fol p{font-weight:640;font-size:calc(52px*var(--s));line-height:1.2;color:rgba(255,255,255,.85);margin-top:calc(26px*var(--s));max-width:20ch;text-wrap:balance}
.fbtn{margin-top:calc(54px*var(--s));background:var(--acc);color:var(--on);font:800 calc(44px*var(--s)) 'Bric';padding:28px 90px;border-radius:999px}
.hd{color:rgba(255,255,255,.6)}
.grid i{border-radius:24%;background:rgba(255,255,255,.14)}
"""

LOOK_CSS = {"impacto": CSS_IMPACTO, "caderno": CSS_CADERNO, "recorte": CSS_RECORTE, "tela": CSS_TELA}


def initials(handle):
    h = re.sub(r"[^a-zA-Z]", "", handle or "")
    return (h[:2] or "··").lower()


def scraps_html(text, rnd, turn_cls="w-t"):
    """manchete em papéis recortados; trecho entre ** usa turn_cls"""
    out = []
    pal = ["w-a", "w-b", "w-a", "w-d", "w-c", "w-a"]
    parts = re.split(r"(\*\*.+?\*\*)", text or "")
    k = 0
    for part in parts:
        turn = part.startswith("**")
        words = part.strip("*").split()
        for w in words:
            cls = turn_cls if turn else pal[k % len(pal)]
            k += 1
            rot = rnd.uniform(-3.2, 3.2)
            out.append(f"<span class='scrap {cls}' style='transform:rotate({rot:.1f}deg)'>{esc(w)}</span>")
    return " ".join(out)


def build(look, data, s, i, total, fmt):
    if look in GEN_LOOKS:
        return gen_build(look, data, s, i, total, fmt)
    pil = PILLARS[data["pilar"]]
    k = s.get("type", "story")
    handle = esc(data.get("handle", ""))
    rnd = random.Random(f"{data.get('slug')}-{look}-{i}")
    tall = fmt == "tiktok"
    S = 1.08 if tall else 1.0
    acc, dark, on = pil["acc"], pil["dark"], pil["on"]
    acct = text_acc(acc)
    v = {"bg": "#EDEDEA", "fg": INK, "muted": "#5a5a5a", "track": "rgba(18,18,18,.14)", "progc": acc, "nextc": acct, "acct": acct}
    pill = False
    body = ""
    show_hd = show_prog = show_next = True
    grain = True

    # ------------------------------ IMPACTO ------------------------------
    if look == "impacto":
        if k == "cover":
            v.update(bg=dark, fg="#fff")
            stat = (f"<div class='cstat'><b>{esc(s['stat'])}</b><span>{esc(s.get('stat_label', ''))}</span></div>"
                    if s.get("stat") else "")
            body = (f"<div class='bloom'></div>{SPOT if s.get('art') == 'spotlight' else ''}<div class='chandle'>{handle}</div>"
                    f"<div class='cwrap'>{stat}<h1 data-fit='{int(170 * S)}'>{stars(s['title'].upper(), 'turn')}</h1>"
                    f"<div class='swipe'><span></span>Arraste{ARROW_SVG.format(s=48, bg=acc, fg=on)}</div></div>")
            show_hd = show_prog = show_next = False
        elif k == "story":
            body = f"<div class='wrap'>{paras(s['text'])}</div>"
        elif k == "big":
            darkt = s.get("tone") == "dark"
            v.update(bg=dark if darkt else acc, fg="#fff" if darkt else on, hl=acc if darkt else YEL,
                     track="rgba(255,255,255,.22)" if (darkt or on == "#FFFFFF") else "rgba(18,18,18,.18)",
                     progc="#fff" if (darkt or on == "#FFFFFF") else INK, nextc="#fff" if darkt else on, muted="rgba(255,255,255,.65)" if (darkt or on == "#FFFFFF") else "rgba(18,18,18,.6)")
            pill = not darkt
            body = (f"<div class='wrap big{'' if darkt else ' onacc'}'><p data-fit='{int(210 * S)}' style='--hl:{acc if darkt else YEL}'>"
                    f"{stars(s['text'].upper(), 'hi')}</p></div>")
        elif k == "reveal":
            v.update(bg=dark, fg="#fff", track="rgba(255,255,255,.22)", muted="rgba(255,255,255,.6)", nextc=acc)
            body = (f"<div class='wrap'><div class='rnum' data-fitw='{int(560 * S)}'>{esc(s['number'])}</div>"
                    f"<p class='rtext'>{mark(s.get('text', ''))}</p></div>")
        elif k == "dots":
            v.update(bg=dark, fg="#fff", track="rgba(255,255,255,.22)", muted="rgba(255,255,255,.6)", nextc=acc)
            body = dots_block(s, S)
        elif k == "follow":
            v.update(bg=dark, fg="#fff", track="rgba(255,255,255,.22)", muted="rgba(255,255,255,.6)")
            txt = esc(s.get("text", "Siga {handle} pra não perder a próxima.")).replace("\n", "<br>").replace(
                "{handle}", f"<span class='fh'>{handle}</span>")
            body = f"<div class='bloom'></div><div class='wrap fol'><p data-fit='{int(110 * S)}'>{txt}</p></div>"
            show_next = False
        else:
            body = common_block(k, s, rnd, look, acc, S)

    # ------------------------------ CADERNO ------------------------------
    elif look == "caderno":
        v.update(bg="#FBFAF5", fg=INK, nextc=PEN, progc=PEN, track="rgba(29,63,224,.18)")
        tapes = (f"<div class='tape' style='left:-40px;top:70px;transform:rotate(-24deg)'></div>"
                 f"<div class='tape' style='right:-50px;top:{'140' if tall else '60'}px;transform:rotate(28deg)'></div>")
        if k == "cover":
            stat = ""
            if s.get("stat"):
                stat = (f"<div class='cstat'><span class='hmk'><b>{esc(s['stat'])}</b>{hand_circle(rnd, PEN, 8)}</span>"
                        f"<span>{esc(s.get('stat_label', ''))}</span></div>")
            body = (f"{tapes}<div class='chandle'>{handle}</div>"
                    f"<div class='wrap cw' style='justify-content:flex-start'>{stat}<h1 data-fit='{int(140 * S)}'>{stars(s['title'], 'turn')}</h1>"
                    f"<div class='swipe'>arrasta pro lado{hand_arrow(rnd, PEN, 150, 90)}</div></div>")
            show_hd = show_prog = show_next = False
        elif k == "story":
            body = f"<div class='wrap'>{paras(s['text'])}</div>"
        elif k == "big":
            body = (f"{tapes if i % 2 else ''}<div class='wrap big'><p data-fit='{int(190 * S)}'>{stars(s['text'], 'hi')}</p></div>")
        elif k == "reveal":
            body = (f"<div class='wrap'><div class='rnum' data-fitw='{int(400 * S)}'>{esc(s['number'])}{hand_circle(rnd, '#E24848', 9)}</div>"
                    f"<p class='rtext'>{esc(plain(s.get('text', '')))}</p></div>")
        elif k == "cta":
            kw = esc(s["keyword"]).upper()
            body = (f"<div class='wrap'><p class='clead'>{esc(s.get('lead', ''))}</p><div class='comente'>comente</div>"
                    f"<div class='kw'><span class='hmk'><span data-fitw='{int(220 * S)}'>{kw}</span>{hand_circle(rnd, '#E24848', 9)}</span></div>"
                    f"<p class='sub'>{esc(s.get('sub', ''))}</p></div>")
        elif k == "follow":
            txt = esc(s.get("text", "Siga {handle} pra não perder a próxima.")).replace("\n", "<br>").replace(
                "{handle}", f"<span class='fh'>{handle}</span>")
            body = f"{tapes}<div class='wrap fol'><p data-fit='{int(96 * S)}'>{txt}</p><div class='sig'>— até a próxima</div></div>"
            show_next = False
        else:
            body = common_block(k, s, rnd, look, acc, S)

    # ------------------------------ RECORTE ------------------------------
    elif look == "recorte":
        light_acc = on == "#121212"
        pill = True
        v.update(bg=acc, fg=INK, muted="rgba(18,18,18,.7)" if light_acc else "rgba(255,255,255,.85)",
                 track="rgba(18,18,18,.22)" if light_acc else "rgba(255,255,255,.35)", progc="#121212" if light_acc else "#fff",
                 nextc="#121212" if light_acc else "#fff")
        nextfg = "#121212" if light_acc else "#fff"
        tp = (f"<div class='tape' style='left:{rnd.randint(140, 400)}px;top:{rnd.randint(40, 90) + (110 if tall else 0)}px;"
              f"transform:rotate({rnd.uniform(-12, 12):.0f}deg)'></div>")
        if k == "cover":
            stat = (f"<div class='cstat'><b>{esc(s['stat'])}</b><span>{esc(s.get('stat_label', ''))}</span></div>"
                    if s.get("stat") else "")
            body = (f"<div class='chandle'>{handle}</div><div class='cwrap'>{stat}"
                    f"<div class='title' data-fit='{int(118 * S)}'>{scraps_html(s['title'].upper(), rnd)}</div>"
                    f"<div class='swipe'>Arraste{ARROW_SVG.format(s=40, bg='#121212', fg='#fff')}</div></div>")
            show_hd = show_prog = show_next = False
        elif k == "story":
            rot = rnd.choice([-1.6, -1, 1, 1.4])
            body = (f"<div class='wrap'><div class='card' style='transform:rotate({rot}deg);clip-path:{torn(rnd)}'>{paras(s['text'])}</div>{tp}</div>")
        elif k == "big":
            body = (f"<div class='wrap big'><div class='title' data-fit='{int(150 * S)}'>{scraps_html(s['text'].upper(), rnd, 'w-c')}</div></div>")
        elif k == "reveal":
            body = (f"<div class='wrap'><div class='rbox' style='clip-path:{torn(rnd)}'><div class='rnum' data-fitw='{int(470 * S)}'>"
                    f"{esc(s['number'])}</div></div><p class='rtext'>{mark(s.get('text', ''))}</p>{tp}</div>")
        elif k == "versus":
            body = f"<div class='wrap'><div class='card' style='transform:rotate(-1deg);clip-path:{torn(rnd)}'>{versus_inner(s, look, acc)}</div>{tp}</div>"
        elif k == "cta":
            kw = esc(s["keyword"]).upper()
            body = (f"<div class='wrap'><p class='clead'>{esc(s.get('lead', ''))}</p><div class='comente'>Comente</div>"
                    f"<div class='kw' style='clip-path:{torn(rnd, 10)}'><span data-fitw='{int(220 * S)}'>{kw}</span></div>"
                    f"<p class='sub'>{esc(s.get('sub', ''))}</p></div>")
        elif k == "follow":
            raw = s.get("text", "Siga {handle} pra não perder a próxima.").replace("{handle}", "§H§")
            words = []
            for w in raw.replace("\n", " ").split():
                if "§H§" in w:
                    words.append(f"<span class='scrap w-b' style='transform:rotate({rnd.uniform(-3, 3):.1f}deg)'>{handle}</span>")
                else:
                    words.append(f"<span class='scrap {rnd.choice(['w-a', 'w-d', 'w-a'])}' style='transform:rotate({rnd.uniform(-3, 3):.1f}deg)'>{esc(w)}</span>")
            body = f"<div class='wrap fol'><div class='title' data-fit='{int(110 * S)}'>{' '.join(words)}</div></div>"
            show_next = False
        else:
            body = common_block(k, s, rnd, look, acc, S)
            if k == "chat":
                pass
        v["fg"] = nextfg if k in ("cover", "big", "follow") else v["fg"]

    # ------------------------------ TELA ------------------------------
    elif look == "tela":
        accl = acc if on == "#121212" else f"color-mix(in srgb,{acc} 70%,#fff)"
        v.update(bg="#0B0C10", fg="#fff", muted="rgba(255,255,255,.55)", track="rgba(255,255,255,.2)", progc=acc, nextc=accl)
        ini = initials(data.get("handle", ""))
        if k == "cover":
            stat = (f"<div class='lock'><b>{esc(s['stat'])}</b><span>{esc(s.get('stat_label', ''))}</span></div>"
                    if s.get("stat") else "")
            body = (f"{stat}<div class='cwrap'><div class='notif'><div class='nhead'><div class='app'>{ini}</div>{handle}<em>agora</em></div>"
                    f"<h1 data-fit='{int(96 * S)}'>{stars(s['title'], 'turn')}</h1></div>"
                    f"<div class='swipe'><i></i>deslize para ver</div></div>")
            show_hd = show_prog = show_next = False
        elif k == "story":
            body = (f"<div class='wrap'><div class='note'><div class='ntop'><span>Notas</span><b>{i} de {total}</b></div>"
                    f"{paras(s['text'])}</div></div>")
        elif k == "big":
            body = (f"<div class='wrap big'><div class='search'><svg width='38' height='38' viewBox='0 0 24 24'><circle cx='10.5' cy='10.5' r='6.5' "
                    f"stroke='rgba(255,255,255,.6)' stroke-width='2.4' fill='none'/><path d='M15.5 15.5L21 21' stroke='rgba(255,255,255,.6)' "
                    f"stroke-width='2.4' stroke-linecap='round'/></svg>pesquisar</div>"
                    f"<p data-fit='{int(170 * S)}'>{stars(s['text'], 'hi')}<span class='caret'></span></p></div>")
        elif k == "reveal":
            body = (f"<div class='wrap'><div class='widget'><div class='wlab'><i></i>{handle}</div>"
                    f"<div class='rnum' data-fitw='{int(400 * S)}'>{esc(s['number'])}</div><p class='rtext'>{mark(s.get('text', ''))}</p></div></div>")
        elif k == "versus":
            note = f"<p class='vnote'>{mark(s.get('note', ''))}</p>" if s.get("note") else ""
            rows = "".join(
                f"<div class='vrow'><div class='vlab'><span>{esc(it['label'])}</span><b style='color:{text_acc(acc) if it.get('color', INK).upper() == acc.upper() else it.get('color', INK)}'>"
                f"{esc(it.get('display', str(int(float(it['value']))) + '%'))}</b></div><div class='vbar'><i style='width:{max(float(it['value']), 2.5)}%;"
                f"background:{it.get('color', INK)}'></i></div></div>" for it in s["items"])
            body = f"<div class='wrap'><div class='vpanel'><p class='vtitle'>{mark(s.get('title', ''))}</p>{rows}</div>{note}</div>"
        elif k == "chat":
            lab = f"<p class='clab'>{esc(s.get('label', ''))}</p>" if s.get("label") else ""
            msgs = "".join(f"<div class='msg {m.get('side', 'left')}'><small>{esc(m.get('who', ''))}</small>"
                           f"<div class='bub'>{mark(m['text'])}</div></div>" for m in s["messages"])
            cap = f"<p class='ccap'>{mark(s.get('caption', ''))}</p>" if s.get("caption") else ""
            body = f"<div class='wrap chat'>{lab}{msgs}{cap}</div>"
        elif k == "dots":
            body = dots_block(s, S)
        elif k == "cta":
            kw = esc(s["keyword"]).upper()
            body = (f"<div class='wrap'><p class='clead'>{esc(s.get('lead', ''))}</p><p class='kwlab'>Comente</p>"
                    f"<div class='inputbar' style='margin-top:14px'><div class='typed' data-fitw='{int(130 * S)}'>{kw}<span class='caret'></span></div>"
                    f"<div class='send'><svg width='44' height='44' viewBox='0 0 24 24'><path d='M12 19V5M5 12l7-7 7 7' stroke='{on}' "
                    f"stroke-width='2.6' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg></div></div>"
                    f"<p class='sub'>{esc(s.get('sub', ''))}</p></div>")
        elif k == "follow":
            txt = esc(s.get("text", "Siga {handle} pra não perder a próxima.")).replace("{handle}", handle).replace("\n", "<br>")
            body = (f"<div class='wrap'><div class='profile'><div class='avatar'>{ini}</div><div class='pname'>{handle}</div>"
                    f"<div class='fol'><p>{txt}</p></div><div class='fbtn'>Seguir</div></div></div>")
            show_next = False
        v["accl"] = accl
        v["acc2"] = acc

    v.setdefault("hl", YEL)
    v.setdefault("accl", acc)
    v.setdefault("acc2", acc)
    prog = ("<div class='prog'>" + "".join(f"<i class='{'on' if n < i else ''}'></i>" for n in range(total)) + "</div>") if show_prog else ""
    nxt = f"<div class='next'>continua<b>→</b></div>" if (show_next and i < total) else ""
    hd = f"<div class='hd{' pill' if pill else ''}'>{handle}</div>" if show_hd else ""
    return body + hd + prog + nxt, v, grain


# ---------------- mundos genéricos (looks/<nome>.css) ----------------
def _ln(html_text):
    return f"<span class='ln'>{html_text}</span>"


def tiles(text, hi_cls="hi"):
    """cada letra numa plaquinha (placar); **trecho** recebe hi_cls"""
    out = []
    for part in re.split(r"(\*\*.+?\*\*)", text or ""):
        hi = part.startswith("**")
        for n, word in enumerate(part.strip("*").split(" ")):
            if not word:
                continue
            chars = "".join(f"<i>{esc(c)}</i>" for c in word)
            out.append(f"<span class='w{' ' + hi_cls if hi else ''}'>{chars}</span>")
    return "<span class='tl'>" + "<b class='sp'></b>".join(out) + "</span>"


def barcode(rnd):
    x, bars = 0, ""
    while x < 300:
        w = rnd.choice([2, 2, 3, 4, 6])
        bars += f"<rect x='{x}' y='0' width='{w}' height='60'/>"
        x += w + rnd.choice([2, 3, 4])
    return f"<svg class='barcode' viewBox='0 0 300 60' preserveAspectRatio='none'>{bars}</svg>"


def gen_vars(look, pil, i):
    acc, dark, on = pil["acc"], pil["dark"], pil["on"]
    acct = text_acc(acc)
    light = on == "#121212"
    drench = dict(bg=acc, fg=INK, muted=INK, track="rgba(18,18,18,.22)" if light else "rgba(255,255,255,.35)",
                  progc=INK if light else "#fff", nextc=INK if light else "#fff")
    V = {
        "placar": dict(bg="#0F1114", fg="#F2EFE6", muted="#9A9EA6", track="rgba(255,255,255,.16)", progc=acc, nextc=acc),
        "recibo": drench, "quadrinho": drench, "rotulo": drench, "mural": dict(drench, bg="#B5875A", track="rgba(18,18,18,.25)", progc=INK, nextc=INK),
        "riso": dict(bg="#F3F3F1", fg="#1F2647", muted="#4F5675", track="rgba(31,38,71,.16)", progc=acc, nextc=acct),
        "bauhaus": dict(bg="#E6E4DF", fg=INK, muted="#4a4a4a", track="rgba(18,18,18,.16)", progc=INK, nextc=INK),
        "pixel": dict(bg="#1A1C2C", fg="#F4F4F4", muted="#A3A9C2", track="rgba(255,255,255,.16)", progc=acc, nextc=acc),
        "quadro": dict(bg="#213A2F", fg="#F1F1E8", muted="#B4C2B8", track="rgba(255,255,255,.18)", progc="#F1F1E8", nextc="#F1F1E8"),
        "tabloide": dict(bg="#F5F5F3", fg="#111111", muted="#4a4a4a", track="rgba(17,17,17,.16)", progc="#111", nextc="#111"),
        "telegrama": dict(bg=dark, fg="#F1F1E8", muted="rgba(255,255,255,.62)", track="rgba(255,255,255,.2)", progc=acc, nextc=acc),
    }[look]
    v = dict(V, acct=acct, hl=YEL, accl=acc, acc2=acc)
    return v, look in ("recibo", "quadrinho", "rotulo", "mural")


def gen_build(look, data, s, i, total, fmt):
    pil = PILLARS[data["pilar"]]
    k = s.get("type", "story")
    handle = esc(data.get("handle", ""))
    rnd = random.Random(f"{data.get('slug')}-{look}-{i}")
    S = 1.08 if fmt == "tiktok" else 1.0
    upper = look in ("placar", "tabloide", "bauhaus", "quadrinho")
    T = (lambda t: (t or "").upper()) if upper else (lambda t: t or "")
    tl = look == "placar"
    v, pill = gen_vars(look, pil, i)
    show_hd = show_prog = show_next = True
    deco = ""
    if look == "mural":
        deco = "<div class='pin'></div>"
    if look == "bauhaus":
        cx, cy = rnd.choice([(88, 12), (12, 88), (90, 86), (8, 10)])
        deco = (f"<svg class='bh' viewBox='0 0 100 100' preserveAspectRatio='none'><circle cx='{cx}' cy='{cy}' r='{rnd.randint(16, 24)}' "
                f"style='fill:var(--acc)'/><rect x='{rnd.choice([0, 94])}' y='0' width='6' height='100' fill='#121212'/></svg>")
    if k == "cover":
        stat = ""
        if s.get("stat"):
            num = tiles(s["stat"]) if tl else esc(s["stat"])
            stat = f"<div class='cstat'><b>{num}</b><span>{esc(s.get('stat_label', ''))}</span></div>"
        bar = barcode(rnd) if look == "recibo" else ""
        body = (f"{deco if look == 'bauhaus' else ''}<div class='chandle'>{handle}</div><div class='wrap cw' style='justify-content:flex-start'><div class='panel'>{deco if look == 'mural' else ''}"
                f"{stat}<h1 data-fit='{int(130 * S)}'>{_ln(stars(T(s['title']), 'turn'))}</h1>{bar}</div>"
                f"<div class='swipe'>Arraste{ARROW_SVG.format(s=40, bg='var(--acc)', fg='var(--on)')}</div></div>")
        show_hd = show_prog = show_next = False
    elif k == "story":
        parts = [p.strip() for p in (s.get("text") or "").split("\n\n") if p.strip()]
        ps = "".join(f"<p class='{'lead' if n == 0 else 'rest'}'>{_ln(mark(p))}</p>" for n, p in enumerate(parts))
        body = f"{deco if look == 'bauhaus' else ''}<div class='wrap'><div class='panel'>{deco if look == 'mural' else ''}{ps}</div></div>"
    elif k == "big":
        txt = tiles(T(s["text"])) if tl else _ln(stars(T(s["text"]), "hi"))
        body = f"{deco if look == 'bauhaus' else ''}<div class='wrap big'><div class='panel'>{deco if look == 'mural' else ''}<p data-fit='{int(170 * S)}'>{txt}</p></div></div>"
    elif k == "reveal":
        num = tiles(s["number"]) if tl else esc(s["number"])
        body = (f"{deco if look == 'bauhaus' else ''}<div class='wrap'><div class='panel'>{deco if look == 'mural' else ''}<div class='rnum' data-fitw='{int(440 * S)}'>{num}</div>"
                f"<p class='rtext'>{_ln(mark(s.get('text', '')))}</p></div></div>")
    elif k == "versus":
        body = f"<div class='wrap'><div class='panel'>{deco if look == 'mural' else ''}{versus_inner(s, look, pil['acc'])}</div></div>"
    elif k == "chat":
        body = common_block(k, s, rnd, look, pil["acc"], S)
    elif k == "dots":
        tot = max(1, min(int(s.get("total", 100)), 100))
        on = max(0, min(int(s.get("value", 0)), tot))
        cols = tot if tot <= 5 else (5 if tot <= 10 else 10)
        cells = "".join(f"<i class='{'on' if n < on else ''}'></i>" for n in range(tot))
        body = (f"<div class='wrap'><div class='panel'>{deco if look == 'mural' else ''}<div class='grid' style='--n:{cols}'>{cells}</div>"
                f"<p class='rtext'>{_ln(mark(s.get('text', '')))}</p></div></div>")
    elif k == "cta":
        kw = esc(s["keyword"]).upper()
        kwh = tiles(kw) if tl else kw
        bar = barcode(rnd) if look == "recibo" else ""
        body = (f"<div class='wrap'><div class='panel'>{deco if look == 'mural' else ''}<p class='clead'>{_ln(esc(s.get('lead', '')))}</p>"
                f"<div class='comente'>Comente</div><div class='kw'><span data-fitw='{int(200 * S)}'>{kwh}</span></div>"
                f"<p class='sub'>{_ln(esc(s.get('sub', '')))}</p>{bar}</div></div>")
    else:
        txt = esc(T(s.get("text", "Siga {handle} pra não perder a próxima."))).replace("\n", "<br>").replace(
            "{HANDLE}" if upper else "{handle}", f"<span class='fh'>{handle}</span>")
        body = f"{deco if look == 'bauhaus' else ''}<div class='wrap fol'><div class='panel'>{deco if look == 'mural' else ''}<p data-fit='{int(110 * S)}'>{_ln(txt)}</p></div></div>"
        show_next = False
    prog = ("<div class='prog'>" + "".join(f"<i class='{'on' if n < i else ''}'></i>" for n in range(total)) + "</div>") if show_prog else ""
    nxt = "<div class='next'>continua<b>→</b></div>" if (show_next and i < total) else ""
    hd = f"<div class='hd{' pill' if pill else ''}'>{handle}</div>" if show_hd else ""
    return body + hd + prog + nxt, v, True


def dots_block(s, S):
    tot = max(1, min(int(s.get("total", 100)), 100))
    on = max(0, min(int(s.get("value", 0)), tot))
    cols = tot if tot <= 5 else (5 if tot <= 10 else 10)
    cells = "".join(f"<i class='{'on' if n < on else ''}'></i>" for n in range(tot))
    gw = int((760 if tot > 10 else 928) * S)
    return (f"<div class='wrap'><div class='grid' style='--n:{cols};width:{gw}px'>{cells}</div>"
            f"<p class='rtext'>{mark(s.get('text', ''))}</p></div>")


def versus_inner(s, look, acc=""):
    rows = ""
    for it in s["items"]:
        val = float(it["value"])
        c = it.get("color", INK)
        ct = text_acc(c) if c.upper() == acc.upper() else c
        rows += (f"<div class='vrow' style='color:{c}'><div class='vlab'>{esc(it['label'])}</div>"
                 f"<div class='vnum' style='color:{ct}'>{esc(it.get('display', str(int(val)) + '%'))}</div>"
                 f"<div class='vbar'><i style='width:{max(val, 2.5)}%;background-color:{c}'></i></div></div>")
    note = f"<p class='vnote'>{mark(s.get('note', ''))}</p>" if s.get("note") else ""
    return f"<p class='vtitle'>{mark(s.get('title', ''))}</p>{rows}{note}"


def common_block(k, s, rnd, look, acc, S):
    if k == "versus":
        return f"<div class='wrap'>{versus_inner(s, look, acc)}</div>"
    if k == "chat":
        lab = f"<p class='clab'>{esc(s.get('label', ''))}</p>" if s.get("label") else ""
        msgs = "".join(f"<div class='msg {m.get('side', 'left')}'><small>{esc(m.get('who', ''))}</small>"
                       f"<div class='bub'>{mark(m['text'])}</div></div>" for m in s["messages"])
        cap = f"<p class='ccap'>{mark(s.get('caption', ''))}</p>" if s.get("caption") else ""
        return f"<div class='wrap chat'>{lab}{msgs}{cap}</div>"
    if k == "cta":
        kw = esc(s["keyword"]).upper()
        return (f"<div class='wrap'><p class='clead'>{esc(s.get('lead', ''))}</p><div class='comente'>COMENTE</div>"
                f"<div class='kw'>{brush(rnd, YEL)}<span data-fitw='{int(240 * S)}'>{kw}</span></div>"
                f"<p class='sub'>{esc(s.get('sub', ''))}</p></div>")
    if k == "story":
        return f"<div class='wrap'>{paras(s.get('text', ''))}</div>"
    if k == "dots":
        return dots_block(s, S)
    return ""


FIT_JS = """
<script>
document.fonts.ready.then(()=>{
  document.querySelectorAll('[data-fit]').forEach(el=>{
    const box=el.closest('.wrap,.cwrap,.notif')||el.parentElement; let s=+el.dataset.fit; el.style.fontSize=s+'px';
    const over=()=>box.scrollHeight>box.clientHeight+14||el.scrollWidth>el.clientWidth+(el.classList.contains('title')?40:1)||document.body.scrollHeight>document.body.clientHeight+1;
    while(s>34 && over()){s-=2;el.style.fontSize=s+'px';}
  });
  document.querySelectorAll('[data-fitw]').forEach(el=>{
    const wrap=el.closest('.wrap'); const lim=(wrap?wrap.clientWidth:900)-PXX*2-60; let s=+el.dataset.fitw; el.style.fontSize=s+'px';
    const w=()=>Math.max(el.scrollWidth,el.offsetWidth);
    while(s>50 && w()>lim){s-=2;el.style.fontSize=s+'px';}
    const b=el.parentElement.querySelector('.brush'); if(b) b.style.width=(el.offsetWidth*1.02)+'px';
  });
  document.body.dataset.ready='1';
});
</script>"""


EXTRA_FONTS = [
    ("Big", "@fontsource-variable/big-shoulders-display/files/big-shoulders-display-latin-wght-normal.woff2", "100 900"),
    ("Bang", "@fontsource/bangers/files/bangers-latin-400-normal.woff2", "400"),
    ("Pix", "@fontsource-variable/pixelify-sans/files/pixelify-sans-latin-wght-normal.woff2", "400 700"),
    ("Type", "@fontsource/special-elite/files/special-elite-latin-400-normal.woff2", "400"),
    ("Mono", "@fontsource-variable/red-hat-mono/files/red-hat-mono-latin-wght-normal.woff2", "300 700"),
    ("Marker", "@fontsource/permanent-marker/files/permanent-marker-latin-400-normal.woff2", "400"),
    ("Arch", "@fontsource-variable/archivo/files/archivo-latin-standard-normal.woff2", "100 900"),
]


def look_css(look):
    if look not in GEN_LOOKS:
        return LOOK_CSS[look]
    css = (LOOK_DIR / "_base.css").read_text(encoding="utf-8") + (LOOK_DIR / f"{look}.css").read_text(encoding="utf-8")
    return re.sub(r"«(\d+)»", r"calc(\1px*var(--s))", css)


def page(data, s, i, total, fmt, font_dir, look):
    w, h = SIZES[fmt]
    tall = fmt == "tiktok"
    S = 1.08 if tall else 1.0
    pt, pb, px = (250, 330, 76) if tall else (100, 150, 76)
    pil = PILLARS[data["pilar"]]
    body, v, grain = build(look, data, s, i, total, fmt)
    fd = Path(font_dir)
    bric = fd / "@fontsource-variable/bricolage-grotesque/files/bricolage-grotesque-latin-standard-normal.woff2"
    kal = fd / "@fontsource/kalam/files/kalam-latin-700-normal.woff2"
    glk = fd / "@fontsource/gloock/files/gloock-latin-400-normal.woff2"
    root = (f":root{{--w:{w}px;--h:{h}px;--s:{S};--pt:{pt}px;--pb:{pb}px;--px:{px}px;--acc:{pil['acc']};--dark:{pil['dark']};"
            f"--on:{pil['on']};--bg:{v['bg']};--fg:{v['fg']};--muted:{v['muted']};--track:{v['track']};--progc:{v['progc']};"
            f"--nextc:{v['nextc']};--hl:{v['hl']};--accl:{v['accl']};--acc2:{v['acc2']};--acct:{v['acct']}}}")
    fonts = (f"@font-face{{font-family:'Bric';src:url('{bric.as_uri()}') format('woff2');font-weight:200 800;font-stretch:75% 100%}}"
             f"@font-face{{font-family:'Hand';src:url('{kal.as_uri()}') format('woff2');font-weight:700}}"
             f"@font-face{{font-family:'Gloock';src:url('{glk.as_uri()}') format('woff2');font-weight:400}}")
    for fam, rel, wt in EXTRA_FONTS:
        fonts += f"@font-face{{font-family:'{fam}';src:url('{(fd / rel).as_uri()}') format('woff2');font-weight:{wt}}}"
    k = s.get("type", "story")
    # fundo especial por slide (impacto usa cor do pilar/escuro em alguns tipos)
    extra = ""
    if look == "impacto" and k in ("cover", "reveal", "follow") or (look == "impacto" and k == "big"):
        extra = "body{background:var(--bg)}"
    if look == "caderno" and k == "big":
        extra = "body{background-color:color-mix(in srgb,var(--acc) 22%,#FBFAF5)}"
    return (f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><style>{fonts}{root}{BASE_CSS}{look_css(look)}{extra}</style>"
            f"</head><body class='{'grain' if grain else ''} look-{look} t-{k}'>{body}{FIT_JS.replace('PXX', str(px))}</body></html>")


def main():
    spec, out = Path(sys.argv[1]), Path(sys.argv[2])
    font_dir = os.environ.get("FONT_DIR", str(Path.cwd() / "node_modules"))
    data = json.loads(spec.read_text(encoding="utf-8"))
    look = data.get("look", "impacto")
    if look not in LOOKS:
        print(f"look desconhecido '{look}', usando impacto", file=sys.stderr)
        look = "impacto"
    slug = data.get("slug", spec.stem)
    total = len(data["slides"])
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    files = []
    with sync_playwright() as p:
        exe = next((c for c in ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"] if os.path.exists(c)), None)
        args = ["--no-sandbox", "--allow-file-access-from-files"]
        b = p.chromium.launch(executable_path=exe, args=args) if exe else p.chromium.launch(args=args)
        for fmt, (w, h) in SIZES.items():
            if os.environ.get("ONLY") and fmt != os.environ["ONLY"]:
                continue
            pg = b.new_page(viewport={"width": w, "height": h})
            for i, s in enumerate(data["slides"], 1):
                hp = tmp / f"{fmt}_{i}.html"
                hp.write_text(page(data, s, i, total, fmt, font_dir, look), encoding="utf-8")
                pg.goto(hp.as_uri(), wait_until="load")
                pg.wait_for_function("document.body.dataset.ready==='1'", timeout=8000)
                pg.wait_for_timeout(80)
                bad = pg.evaluate("""() => {
                  const ws=[...document.querySelectorAll('.wrap,.cwrap')];
                  const over=ws.some(w=>w.scrollHeight>w.clientHeight+16||w.scrollWidth>w.clientWidth+16);
                  const fonts=[...document.fonts].filter(f=>f.status==='error').map(f=>f.family);
                  const P=c=>{const n=c.match(/[0-9.]+/g).map(Number);return c.startsWith('color(')?[n[0]*255,n[1]*255,n[2]*255].concat(n.slice(3)):n};
                  const Lu=a=>{const f=v=>(v/=255)<=.03928?v/12.92:((v+.055)/1.055)**2.4;return .2126*f(a[0])+.7152*f(a[1])+.0722*f(a[2])};
                  const bgOf=e=>{for(;e;e=e.parentElement){const s=getComputedStyle(e),b=P(s.backgroundColor);if(b.length<4||b[3]>.5)return b;if(s.backgroundImage!=='none')return null}return [255,255,255]};
                  const low=[];
                  document.querySelectorAll('body *').forEach(e=>{
                    if(e.tagName==='SCRIPT'||![...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))return;
                    const b=bgOf(e); if(!b)return; const c=P(getComputedStyle(e).color), a=c.length>3?c[3]:1;
                    const m=c.slice(0,3).map((v,j)=>v*a+b[j]*(1-a)); const x=Lu(m), y=Lu(b);
                    const r=(Math.max(x,y)+.05)/(Math.min(x,y)+.05);
                    if(r<3)low.push(e.textContent.trim().slice(0,24)+' '+r.toFixed(1)+':1');
                  });
                  return {over, fonts, low};
                }""")
                f = out / f"{slug}_{fmt}_{i:02d}.png"
                pg.screenshot(path=str(f))
                files.append(str(f))
                if bad["over"]:
                    print(f"OVERFLOW {f.name}", file=sys.stderr)
                if bad["low"]:
                    print(f"CONTRASTE BAIXO {bad['low']} em {f.name}", file=sys.stderr)
                if bad["fonts"]:
                    print(f"FONTE NAO CARREGOU {bad['fonts']} em {f.name}", file=sys.stderr)
            pg.close()
        b.close()
    print("\n".join(files))


if __name__ == "__main__":
    main()
