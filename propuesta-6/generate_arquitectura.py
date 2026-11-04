#!/usr/bin/env python3
"""Genera los diagramas de la propuesta 6 (una arquitectura, dos modos).

Salida:
  arquitectura-diagrama.svg / .png  -> solo el diagrama
  arquitectura.svg / .png           -> diagrama + tabla de costos

Sin dependencias de Python. El PNG se genera con `rsvg-convert`
(brew install librsvg) si está disponible; el SVG se ve directo en GitHub.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
W = 1820
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "Menlo, SF Mono, Consolas, monospace"

C = {
    "bg": "#f8fafc",
    "ink": "#0f172a",
    "muted": "#475569",
    "soft": "#94a3b8",
    "line": "#cbd5e1",
    "arrow": "#64748b",
    # modo demo (nube)
    "demo": "#4f46e5",
    "demo_bg": "#eef2ff",
    "demo_slot": "#ffffff",
    "demo_ink": "#312e81",
    # modo local (datacenter)
    "local": "#059669",
    "local_bg": "#ecfdf5",
    "local_slot": "#ffffff",
    "local_ink": "#064e3b",
    # voice-agent
    "agent": "#d97706",
    "agent_bg": "#fffbeb",
    "agent_ink": "#78350f",
    # núcleo
    "core": "#0f172a",
    "core_card": "#1e293b",
    "core_line": "#334155",
    "core_ink": "#f8fafc",
    "core_soft": "#94a3b8",
    "accent": "#f59e0b",
}


def text(x, y, s, size=14, weight="400", fill=None, anchor="start", family=FONT, extra=""):
    fill = fill or C["ink"]
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{escape(s)}</text>'
    )


def rect(x, y, w, h, rx=12, fill="#fff", stroke="none", sw=1.5, extra=""):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
    )


def path(d, stroke=None, sw=2, fill="none", dash=None, marker="arrow", extra=""):
    stroke = stroke or C["arrow"]
    dash_attr = f'stroke-dasharray="{dash}"' if dash else ""
    m = f'marker-end="url(#{marker})"' if marker else ""
    return (
        f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
        f'stroke-linecap="round" stroke-linejoin="round" {dash_attr} {m} {extra}/>'
    )


def badge(x, y, n, color):
    return (
        f'<circle cx="{x}" cy="{y}" r="13" fill="{color}" stroke="#fff" stroke-width="2.5"/>'
        + text(x, y + 5, str(n), 13, "700", "#fff", "middle")
    )


# --------------------------------------------------------------------------- iconos


def icon_cloud(x, y, color):
    return (
        f'<path transform="translate({x},{y}) scale(1.1)" fill="{color}" '
        'd="M6 18h13a5 5 0 0 0 .5-9.97A7 7 0 0 0 6.2 9.5 4.5 4.5 0 0 0 6 18z"/>'
    )


def icon_server(x, y, color):
    out = []
    for i in range(3):
        yy = y + i * 9
        out.append(rect(x, yy, 26, 7, 2, color))
        out.append(f'<circle cx="{x + 21}" cy="{yy + 3.5}" r="1.6" fill="#fff"/>')
    return "".join(out)


def icon_phone(cx, cy):
    return (
        rect(cx - 22, cy - 36, 44, 72, 9, C["ink"])
        + rect(cx - 17, cy - 28, 34, 50, 3, "#38bdf8")
        + f'<circle cx="{cx}" cy="{cy + 29}" r="3" fill="#475569"/>'
        # ondas de llamada
        + path(f"M{cx + 30} {cy - 22} q 9 9 0 18", C["accent"], 3, marker=None)
        + path(f"M{cx + 38} {cy - 30} q 16 17 0 34", C["accent"], 3, marker=None)
    )


# --------------------------------------------------------------------------- piezas

SLOT_W, SLOT_GAP, SLOT_X0 = 144, 14, 310
LANE_X, LANE_W = 290, 5 * 144 + 4 * 14 + 40

DEMO_SLOTS = [
    ("TELEFONÍA", "Número LiveKit", "listo en minutos"),
    ("SERVIDOR DE VOZ", "LiveKit Cloud", "SIP · salas · ruido"),
    ("VOZ → TEXTO", "Deepgram", "streaming en español"),
    ("CLASIFICA", "Claude Haiku 5.5", "sí · no · persona"),
    ("TEXTO → VOZ", "Deepgram Aura-2", "voz colombiana"),
]
LOCAL_SLOTS = [
    ("TELEFONÍA", "Troncal SIP", "operador colombiano"),
    ("SERVIDOR DE VOZ", "LiveKit OSS", "en el datacenter"),
    ("VOZ → TEXTO", "Faster-Whisper", "GPU"),
    ("CLASIFICA", "LLM local", "Ollama / vLLM · CPU"),
    ("TEXTO → VOZ", "Piper", "CPU"),
]


def slot_cx(i):
    return SLOT_X0 + i * (SLOT_W + SLOT_GAP) + SLOT_W / 2


def lane(y, h, color, bg, ink, title, tag, icon, slots, slot_y):
    out = [
        rect(LANE_X, y, LANE_W, h, 18, bg, color, 2, 'filter="url(#shadow)"'),
        icon,
        text(LANE_X + 62, y + 36, title, 17, "800", ink, extra='letter-spacing="1.2"'),
    ]
    tag_w = 9.5 * len(tag) + 28
    out.append(rect(LANE_X + LANE_W - tag_w - 18, y + 16, tag_w, 28, 14, color))
    out.append(text(LANE_X + LANE_W - 18 - tag_w / 2, y + 35, tag, 13, "600", "#fff", "middle"))
    for i, (cat, name, sub) in enumerate(slots):
        sx = SLOT_X0 + i * (SLOT_W + SLOT_GAP)
        out.append(rect(sx, slot_y, SLOT_W, 140, 12, "#fff", color, 1.5))
        out.append(rect(sx, slot_y, SLOT_W, 6, 3, color))
        out.append(text(sx + SLOT_W / 2, slot_y + 32, cat, 11, "700", C["soft"], "middle",
                        extra='letter-spacing="1"'))
        out.append(text(sx + SLOT_W / 2, slot_y + 72, name, 16, "700", ink, "middle"))
        out.append(text(sx + SLOT_W / 2, slot_y + 98, sub, 12.5, "400", C["muted"], "middle"))
        if i < len(slots) - 1:
            ax = sx + SLOT_W + 2
            out.append(path(f"M{ax} {slot_y + 70} l 9 0", color, 2, marker="arrow_small"))
    return "".join(out)


def hexagon(cx, cy, r):
    pts = []
    for k in range(6):
        a = math.radians(60 * k)
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return " ".join(pts)


def hex_left_x(cx, cy, r, y):
    """x del borde izquierdo del hexágono (vértice plano a izquierda) a la altura y."""
    h = r * math.sqrt(3) / 2
    return cx - r + abs(y - cy) / h * (r / 2)


# --------------------------------------------------------------------------- diagrama


def diagram():
    out = []

    # Título
    out.append(text(40, 58, "Propuesta 6 — Una arquitectura, dos modos", 32, "800"))
    out.append(text(40, 92,
                    "Demo por llamada en 1 semana en la nube. El día que el cliente lo pida "
                    "(protección de datos o costo), se muda a su datacenter cambiando "
                    "configuración, no código.", 16, "400", C["muted"]))

    # Operador
    ox, oy = 145, 455
    out.append(rect(40, 340, 210, 230, 18, "#fff", C["line"], 1.5, 'filter="url(#shadow)"'))
    out.append(icon_phone(ox - 12, oy - 50))
    out.append(text(ox, oy + 22, "Operador en el puesto", 16, "700", anchor="middle"))
    for k, s in enumerate(["tableta sin internet", "tableta no enciende", "no puede loguearse"]):
        out.append(text(ox, oy + 48 + k * 21, s, 13, "400", C["muted"], "middle"))
    out.append(text(ox, 322, "marca el número de soporte", 13, "600", C["muted"], "middle"))

    # Carriles
    demo_y, local_y = 150, 500
    out.append(lane(demo_y, 230, C["demo"], C["demo_bg"], C["demo_ink"],
                    "MODO DEMO · NUBE", "semana 1 · pagás por minuto",
                    icon_cloud(LANE_X + 22, demo_y + 14, C["demo"]),
                    DEMO_SLOTS, demo_y + 60))
    out.append(lane(local_y, 230, C["local"], C["local_bg"], C["local_ink"],
                    "MODO LOCAL · DATACENTER DEL CLIENTE", "cuando lo pida · pagás hardware",
                    icon_server(LANE_X + 22, local_y + 18, C["local"]),
                    LOCAL_SLOTS, local_y + 60))

    # Conmutador entre carriles
    for i in range(5):
        x = slot_cx(i)
        out.append(path(f"M{x} {demo_y + 238} L{x} {local_y - 8}", C["soft"], 2, dash="4 6",
                        marker="arrow_soft", extra='marker-start="url(#arrow_soft_rev)"'))
    pill_w, pill_cx, pill_cy = 560, LANE_X + LANE_W / 2, (demo_y + 230 + local_y) / 2
    out.append(rect(pill_cx - pill_w / 2, pill_cy - 22, pill_w, 44, 22, C["ink"]))
    out.append(text(pill_cx, pill_cy + 6, "misma interfaz por pieza  ·  se cambia con 1 variable de entorno",
                    15, "600", "#fff", "middle"))

    # Fork operador → carriles
    fy_demo, fy_local = demo_y + 130, local_y + 130
    out.append(path(f"M250 {oy} L270 {oy}", C["arrow"], 2.5, marker=None))
    out.append(path(f"M270 {oy} L270 {fy_demo + 14} Q270 {fy_demo} 284 {fy_demo} L{SLOT_X0 - 3} {fy_demo}",
                    C["demo"], 2.5))
    out.append(path(f"M270 {oy} L270 {fy_local - 14} Q270 {fy_local} 284 {fy_local} L{SLOT_X0 - 3} {fy_local}",
                    C["local"], 2.5))
    out.append(badge(270, oy, 1, C["accent"]))

    # voice-agent (columna)
    bx, bw, by, bh = 1124, 104, 150, 580
    out.append(rect(bx, by, bw, bh, 18, C["agent_bg"], C["agent"], 2.5, 'filter="url(#shadow)"'))
    rcx, rcy = bx + bw / 2, by + bh / 2
    rot = f'transform="rotate(-90 {rcx} {rcy})"'
    out.append(text(rcx, rcy - 14, "voice-agent · LiveKit Agents", 22, "800", C["agent_ink"], "middle", extra=rot))
    out.append(text(rcx, rcy + 14, "MISMO CÓDIGO EN LOS DOS MODOS", 13, "700", C["agent"], "middle",
                    extra=rot + ' letter-spacing="1.5"'))
    out.append(text(rcx, rcy + 36, "DTMF · espera activa · enmascara cédula", 12.5, "400", C["agent_ink"],
                    "middle", extra=rot))
    for fy, col in ((fy_demo, C["demo"]), (fy_local, C["local"])):
        out.append(path(f"M{LANE_X + LANE_W} {fy} L{bx - 4} {fy}", col, 2.5))
    out.append(badge(LANE_X + LANE_W + 12, fy_demo - 22, 2, C["accent"]))
    out.append(badge(LANE_X + LANE_W + 12, fy_local - 22, 2, C["accent"]))

    # Núcleo hexagonal
    hcx, hcy, hr = 1575, 440, 212
    out.append(f'<polygon points="{hexagon(hcx, hcy, hr + 10)}" fill="none" stroke="{C["accent"]}" '
               f'stroke-width="2" stroke-dasharray="2 7" stroke-linecap="round"/>')
    out.append(f'<polygon points="{hexagon(hcx, hcy, hr)}" fill="{C["core"]}" filter="url(#shadow)"/>')
    out.append(text(hcx, hcy - 128, "NÚCLEO PROPIO", 20, "800", C["core_ink"], "middle",
                    extra='letter-spacing="2"'))
    out.append(text(hcx, hcy - 106, "no cambia nunca · hexagonal", 13, "500", C["accent"], "middle"))
    cards = [
        ("Motor YAML", "3 flujos · determinista"),
        ("Postgres", "sesión · casos · historial"),
        ("Reglas de escalamiento", "2–3 intentos · persona"),
    ]
    for k, (t1, t2) in enumerate(cards):
        cy = hcy - 84 + k * 62
        out.append(rect(hcx - 130, cy, 260, 52, 10, C["core_card"], C["core_line"], 1))
        out.append(text(hcx, cy + 22, t1, 15, "700", C["core_ink"], "middle"))
        out.append(text(hcx, cy + 41, t2, 12, "400", C["core_soft"], "middle"))
    out.append(rect(hcx - 82, hcy + 112, 164, 26, 13, "none", C["accent"], 1.5))
    out.append(text(hcx, hcy + 130, "docker-compose.yml", 12.5, "600", C["accent"], "middle", family=MONO))

    # Puertos: voice-agent → núcleo
    for k, (label, y) in enumerate((("next_step()", hcy - 40), ("create_case()", hcy + 40))):
        ex = hex_left_x(hcx, hcy, hr, y)
        out.append(path(f"M{bx + bw} {y} L{ex - 4} {y}", C["accent"], 3))
        out.append(rect(ex - 9, y - 9, 18, 18, 4, C["accent"]))
        out.append(text((bx + bw + ex) / 2 - 4, y - 12, label, 12.5, "700", C["agent_ink"], "middle", family=MONO))
        out.append(badge(bx + bw + 16, y + 18, 3 + k, C["accent"]))

    # Consola
    cx0, cy0 = hcx - 135, 680
    out.append(path(f"M{hcx} {hcy + hr * math.sqrt(3) / 2} L{hcx} {cy0 - 4}", C["ink"], 2.5))
    out.append(rect(cx0, cy0, 270, 66, 14, "#fff", C["ink"], 2, 'filter="url(#shadow)"'))
    out.append(text(hcx, cy0 + 28, "Consola de la mesa", 16, "700", anchor="middle"))
    out.append(text(hcx, cy0 + 50, "cola · tomar caso · transcripción", 12.5, "400", C["muted"], "middle"))
    out.append(badge(cx0 - 2, cy0 + 2, 6, C["accent"]))

    # Lazo de devolución
    loop_y = 790
    out.append(path(f"M{hcx} {cy0 + 66} L{hcx} {loop_y - 14} Q{hcx} {loop_y} {hcx - 14} {loop_y} "
                    f"L{ox + 14} {loop_y} Q{ox} {loop_y} {ox} {loop_y - 14} L{ox} 574",
                    C["accent"], 2.5, dash="10 7"))
    out.append(rect(700, loop_y - 16, 520, 32, 16, C["bg"]))
    out.append(text(960, loop_y + 5, "la mesa devuelve la llamada al operador · sin transferencia en vivo",
                    14, "600", C["agent_ink"], "middle"))
    out.append(badge(680, loop_y, 7, C["accent"]))

    # Paneles inferiores
    py, ph = 840, 290
    panels = [(40, 560), (620, 560), (1200, 580)]

    # A — flujo
    x, w = panels[0]
    out.append(rect(x, py, w, ph, 16, "#fff", C["line"], 1.5))
    out.append(text(x + 24, py + 38, "Una llamada, paso a paso", 18, "800"))
    steps = [
        "El operador marca el número de soporte.",
        "La telefonía entrega la llamada al voice-agent.",
        "Voz → texto → yes / no / human → next_step().",
        "El núcleo devuelve el texto exacto del YAML. El LLM no redacta.",
        "Si el árbol se agota: create_case() con todo lo intentado.",
        "La consola muestra el caso priorizado a la mesa.",
        "La mesa devuelve la llamada.",
    ]
    for k, s in enumerate(steps):
        yy = py + 72 + k * 30
        out.append(badge(x + 36, yy - 5, k + 1, C["accent"]))
        out.append(text(x + 60, yy, s, 14, "400", C["ink"]))

    # B — mudanza
    x, w = panels[1]
    out.append(rect(x, py, w, ph, 16, C["ink"]))
    out.append(text(x + 24, py + 38, "La mudanza: 5 variables, cero código", 18, "800", "#fff"))
    envs = [
        ("SIP_TRUNK", "livekit-cloud", "operador-co"),
        ("LIVEKIT_URL", "*.livekit.cloud", "voz.cliente.local"),
        ("STT", "deepgram", "whisper"),
        ("CLASSIFIER", "anthropic", "openai-compat"),
        ("TTS", "deepgram", "piper"),
    ]
    for k, (var, a, b) in enumerate(envs):
        yy = py + 78 + k * 32
        out.append(text(x + 24, yy, var, 14, "700", C["accent"], family=MONO))
        out.append(text(x + 180, yy, a, 14, "400", "#a5b4fc", family=MONO))
        out.append(text(x + 345, yy, "→", 14, "700", "#fff", family=MONO))
        out.append(text(x + 370, yy, b, 14, "700", "#6ee7b7", family=MONO))
    out.append(f'<line x1="{x + 24}" y1="{py + 240}" x2="{x + w - 24}" y2="{py + 240}" stroke="#334155"/>')
    out.append(text(x + 24, py + 268, "Núcleo, Postgres y consola: el mismo docker-compose.yml.", 14, "500", "#cbd5e1"))

    # C — qué sale del país
    x, w = panels[2]
    out.append(rect(x, py, w, ph, 16, "#fff", C["line"], 1.5))
    out.append(text(x + 24, py + 38, "¿Qué datos salen del país?", 18, "800"))
    rows = [
        (C["demo"], "DEMO", "Audio y texto pasan por proveedores de EE. UU.",
         "→ solo cédulas ficticias, nunca datos reales."),
        (C["local"], "LOCAL", "Solo la llamada entra por el operador telefónico.",
         "→ transcripción, casos y audio quedan adentro."),
    ]
    for k, (col, tag, l1, l2) in enumerate(rows):
        yy = py + 70 + k * 78
        out.append(rect(x + 24, yy - 16, 66, 24, 12, col))
        out.append(text(x + 57, yy + 1, tag, 12, "800", "#fff", "middle"))
        out.append(text(x + 104, yy + 1, l1, 14, "600"))
        out.append(text(x + 104, yy + 24, l2, 14, "400", C["muted"]))
    out.append(rect(x + 24, py + 222, w - 48, 46, 10, C["agent_bg"], C["agent"], 1.2))
    out.append(text(x + 40, py + 250, "Disparador de mudanza: Ley 1581 (datos) o > 7–10 mil min/mes (costo)",
                    13.5, "600", C["agent_ink"]))

    return "".join(out), py + ph


def cost_band(y0):
    out = []
    out.append(text(40, y0 + 10, "Costo mensual orientativo (US$)", 22, "800"))
    out.append(text(40, y0 + 36,
                    "22 días · 2 incidencias por operador por día · 100 % llamada de 6 min · sin desarrollo ni impuestos. "
                    "Detalle en costos.md.", 14, "400", C["muted"]))
    cols = [(40, 360, "Escenario"), (400, 300, "Modo demo / nube"), (700, 300, "Modo local"), (1000, 780, "Lectura")]
    ty = y0 + 56
    out.append(rect(40, ty, 1740, 44, 10, C["ink"]))
    for x, w, h in cols:
        out.append(text(x + 20, ty + 28, h, 15, "700", "#fff"))
    rows = [
        ("Semana de demo", "≈ 20–80 (una vez)", "—", "Cuentas de prueba, una VM y el número. Cédulas ficticias."),
        ("15 operadores", "≈ 180", "≈ 240", "La nube gana: una GPU para ~1 llamada a la vez no se justifica."),
        ("1.400 operadores", "≈ 5.600", "≈ 2.030", "Local ahorra ≈ 64 %: el minuto de Deepgram + LiveKit Cloud domina."),
    ]
    for k, (a, b, c, d) in enumerate(rows):
        ry = ty + 44 + k * 46
        out.append(rect(40, ry, 1740, 46, 0, "#fff" if k % 2 == 0 else "#f1f5f9"))
        out.append(text(60, ry + 29, a, 15, "700"))
        out.append(text(420, ry + 29, b, 16, "800", C["demo"]))
        out.append(text(720, ry + 29, c, 16, "800", C["local"]))
        out.append(text(1020, ry + 29, d, 14.5, "400", C["muted"]))
    out.append(rect(40, ty, 1740, 44 + 46 * 3, 10, "none", C["line"], 1.5))
    return "".join(out), ty + 44 + 46 * 3


def svg(body, h):
    defs = f"""
<defs>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="6"/>
    <feOffset dy="4" result="b"/>
    <feComponentTransfer><feFuncA type="linear" slope="0.12"/></feComponentTransfer>
    <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/>
  </marker>
  <marker id="arrow_small" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
    <path d="M0 0 L10 5 L0 10 z" fill="{C['soft']}"/>
  </marker>
  <marker id="arrow_soft" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0 0 L10 5 L0 10 z" fill="{C['soft']}"/>
  </marker>
  <marker id="arrow_soft_rev" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M10 0 L0 5 L10 10 z" fill="{C['soft']}"/>
  </marker>
</defs>"""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">'
        f"{defs}<rect width=\"{W}\" height=\"{h}\" fill=\"{C['bg']}\"/>{body}</svg>"
    )


def render(name, content):
    svg_path = ROOT / f"{name}.svg"
    svg_path.write_text(content, encoding="utf-8")
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-z", "1.5", "-o", str(ROOT / f"{name}.png"), str(svg_path)], check=True)
    print(f"ok {name}")


def main():
    body, bottom = diagram()
    render("arquitectura-diagrama", svg(body, bottom + 40))
    costs, cbottom = cost_band(bottom + 70)
    render("arquitectura", svg(body + costs, cbottom + 40))


if __name__ == "__main__":
    main()
