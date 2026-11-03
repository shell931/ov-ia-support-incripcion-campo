#!/usr/bin/env python3
"""Genera propuesta-4/arquitectura.png (PSTN + misma pila voz que propuesta 1)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "arquitectura.png"
OUT_DIAGRAM = ROOT / "arquitectura-diagrama.png"

W = 1480
MARGIN = 40
BG = "#f8fafc"
WHITE = "#ffffff"

COLORS = {
    "title": "#0f172a",
    "subtitle": "#475569",
    "pstn_bg": "#fef3c7",
    "pstn_border": "#d97706",
    "pstn_text": "#92400e",
    "lk_bg": "#fdf2f8",
    "lk_border": "#db2777",
    "lk_text": "#831843",
    "aws_bg": "#eef2ff",
    "aws_border": "#4f46e5",
    "aws_text": "#312e81",
    "ai_bg": "#fff7ed",
    "ai_border": "#ea580c",
    "ai_text": "#9a3412",
    "data_bg": "#f5f3ff",
    "data_border": "#7c3aed",
    "data_text": "#4c1d95",
    "mesa_bg": "#f0fdf4",
    "mesa_border": "#16a34a",
    "mesa_text": "#14532d",
    "arrow": "#64748b",
    "table_header": "#1e293b",
    "table_row_a": "#ffffff",
    "table_row_b": "#f1f5f9",
    "table_border": "#cbd5e1",
}

PIEZAS = [
    ("Celular del operador", "Campo", "Marca el número de soporte (PSTN).", "Sin datos móviles ni WhatsApp; voz directa."),
    ("Proveedor PSTN", "Nube (Twilio, Telnyx, Zernio…)", "Número DID + minutos entrantes.", "Entrada teléfono normal; SIP hacia LiveKit."),
    ("LiveKit Cloud", "Nube", "Trunk SIP entrante, salas, ruido, despacho.", "Igual que P1; sin Meta WhatsApp."),
    ("voice-agent (ECS Fargate)", "AWS", "LiveKit Agents por llamada.", "Misma pieza que propuesta 1."),
    ("Deepgram + LLM + Cartesia", "API (US)", "STT, clasificación, TTS.", "Mismo pipeline de voz que P1."),
    ("Motor YAML", "Código en voice-agent", "Tres flujos; LLM no redacta.", "Determinismo del procedimiento."),
    ("gateway (ECS Fargate)", "AWS", "API consola; webhooks telefonía (opc.).", "Sin webhook WhatsApp ni worker de chat."),
    ("ElastiCache Redis", "AWS", "Sesión por número llamante.", "Retomar si se corta la llamada."),
    ("RDS Postgres", "AWS", "Casos, historial enmascarado.", "Consola e indicadores."),
    ("S3", "AWS", "Audios presintetizados de pasos.", "Latencia baja en pasos fijos."),
    ("CloudFront + Cognito", "AWS", "Consola web mesa.", "Login por persona."),
    ("SES + SMS (opc.)", "AWS / PSTN", "Correo y SMS con número de caso.", "Sustituye mensaje WhatsApp al escalar."),
]

COSTOS_15 = [
    ("AWS (us-east-1)", "", "≈ 200", "group"),
    ("ECS Fargate", "2× voice-agent + gateway (sin worker chat)", "75", "row"),
    ("RDS, Redis, ALB, NAT, WAF, S3, consola…", "Misma base que propuesta 1", "125", "row"),
    ("Voz e IA", "", "≈ 97", "group"),
    ("LiveKit Cloud Ship", "≈ 4.000 min SIP (100 % llamadas)", "50", "row"),
    ("Deepgram Nova-3", "4.000 × 0,0077", "31", "row"),
    ("LLM + Cartesia", "Clasificación + frases dinámicas", "16", "row"),
    ("Telefonía PSTN", "", "≈ 15", "group"),
    ("Número DID + minutos entrantes", "≈ 4.000 min inbound", "15", "row"),
    ("SMS (opcional)", "Número de caso al escalar", "10", "row"),
    ("Total 15 operadores", "100 % voz  ·  vs ≈ 300 propuesta 1 (WhatsApp)", "≈ 310", "total"),
]

COSTOS_1400 = [
    ("AWS (us-east-1)", "", "≈ 1.050", "group"),
    ("ECS Fargate", "Autoescalado voice-agent; pico ≈ 45 llamadas", "780", "row"),
    ("Resto AWS", "RDS, Redis, NAT, ALB, etc.", "270", "row"),
    ("Voz e IA", "", "≈ 3.250", "group"),
    ("LiveKit + Deepgram + LLM + Cartesia", "≈ 370.000 min/mes", "3.250", "row"),
    ("Telefonía PSTN", "", "≈ 450", "group"),
    ("DID + minutos entrantes", "Tarifa negociable por volumen", "450", "row"),
    ("SMS", "Escalamientos", "80", "row"),
    ("Total 1.400 operadores", "100 % voz  ·  vs ≈ 4.600 propuesta 1", "≈ 4.800", "total"),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded_rect(draw, xy, radius, fill, outline, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_width(text, fnt):
    bbox = fnt.getbbox(text)
    return bbox[2] - bbox[0]


def wrap_text(text, fnt, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if text_width(trial, fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def draw_box(draw, x, y, w, title, lines, style, title_font, body_font, pad=12):
    wrapped = []
    for line in lines:
        wrapped.extend(wrap_text(line, body_font, w - pad * 2))
    title_h = title_font.getbbox("Ag")[3] + 6
    line_h = body_font.getbbox("Ag")[3] + 4
    h = pad * 2 + title_h + len(wrapped) * line_h
    box = (x, y, x + w, y + h)
    rounded_rect(draw, box, 12, style["bg"], style["border"])
    draw.text((x + pad, y + pad), title, fill=style["text"], font=title_font)
    ty = y + pad + title_h
    for line in wrapped:
        draw.text((x + pad, ty), line, fill=style["text"], font=body_font)
        ty += line_h
    return box


def arrow_down(draw, x, y1, y2):
    if y2 - y1 < 14:
        return
    draw.line((x, y1, x, y2 - 10), fill=COLORS["arrow"], width=2)
    draw.polygon([(x, y2), (x - 6, y2 - 10), (x + 6, y2 - 10)], fill=COLORS["arrow"])


def draw_diagram():
    title_font = font(26, bold=True)
    subtitle_font = font(14)
    box_title = font(14, bold=True)
    box_body = font(12)
    label_font = font(12)

    pstn = {"bg": COLORS["pstn_bg"], "border": COLORS["pstn_border"], "text": COLORS["pstn_text"]}
    lk = {"bg": COLORS["lk_bg"], "border": COLORS["lk_border"], "text": COLORS["lk_text"]}
    aws = {"bg": COLORS["aws_bg"], "border": COLORS["aws_border"], "text": COLORS["aws_text"]}
    ai = {"bg": COLORS["ai_bg"], "border": COLORS["ai_border"], "text": COLORS["ai_text"]}
    data = {"bg": COLORS["data_bg"], "border": COLORS["data_border"], "text": COLORS["data_text"]}
    mesa = {"bg": COLORS["mesa_bg"], "border": COLORS["mesa_border"], "text": COLORS["mesa_text"]}

    H = 1320
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw.text((MARGIN, 22), "Propuesta 4 — PSTN + AWS + LiveKit + Deepgram + Cartesia (como propuesta 1)", fill=COLORS["title"], font=title_font)
    draw.text(
        (MARGIN, 58),
        "Sin WhatsApp  ·  operador marca número fijo/móvil  ·  mismo voice-agent y YAML que la propuesta 1",
        fill=COLORS["subtitle"],
        font=subtitle_font,
    )

    cx = W // 2
    bw = 680
    bx = (W - bw) // 2
    y = 92

    op = draw_box(draw, bx, y, bw, "1. Operador (campo)", ["Marca el número de soporte desde el celular"], {"bg": WHITE, "border": "#94a3b8", "text": COLORS["title"]}, box_title, box_body)
    y = op[3] + 28
    tel = draw_box(draw, bx, y, bw, "2. Proveedor PSTN (nube)", ["Número DID Colombia · minutos entrantes · SIP trunk → LiveKit"], pstn, box_title, box_body)
    arrow_down(draw, cx, op[3], tel[1])
    y = tel[3] + 28
    livekit = draw_box(draw, bx, y, bw, "3. LiveKit Cloud", ["Recibe SIP, sala, cancelación de ruido, despacha voice-agent"], lk, box_title, box_body)
    arrow_down(draw, cx, tel[3], livekit[1])
    y = livekit[3] + 28

    col_w = (bw - 16) // 2
    va = draw_box(draw, bx, y, col_w, "4. voice-agent (ECS)", ["LiveKit Agents · WebSocket saliente"], aws, box_title, box_body)
    pipe = draw_box(draw, bx + col_w + 16, y, col_w, "5. Deepgram → LLM → Cartesia", ["Mismo pipeline que propuesta 1"], ai, box_title, box_body)
    row = max(va[3], pipe[3])
    arrow_down(draw, cx, livekit[3], va[1])
    draw.text((bx + col_w + 16 + col_w // 2 - 40, row + 8), "↔", fill=COLORS["arrow"], font=font(16, bold=True))

    y = row + 36
    yaml = draw_box(draw, bx, y, bw, "6. Motor YAML + Redis", ["Sesión por número · tres casos · DTMF si falla STT"], aws, box_title, box_body)
    arrow_down(draw, bx + col_w // 2, va[3], yaml[1])
    arrow_down(draw, bx + col_w + 16 + col_w // 2, pipe[3], yaml[1])

    y = yaml[3] + 28
    s3 = draw_box(draw, bx, y, col_w, "7. S3 — audios de paso", ["Presintetizados con Cartesia"], data, box_title, box_body)
    pg = draw_box(draw, bx + col_w + 16, y, col_w, "8. Postgres — casos", ["Historial enmascarado"], data, box_title, box_body)
    row2 = max(s3[3], pg[3])
    arrow_down(draw, cx, yaml[3], s3[1])

    y = row2 + 28
    esc = draw_box(
        draw, bx, y, bw,
        "9. Si escala",
        ["Voz: número de caso · SMS (opc.) · SES + consola · mesa devuelve llamada PSTN", "Sin transferencia en vivo · sin WhatsApp"],
        mesa, box_title, box_body,
    )
    arrow_down(draw, cx, row2, esc[1])

    draw.text((MARGIN, esc[3] + 24), "gateway (ECS): API consola — no hay worker de chat WhatsApp", fill=COLORS["subtitle"], font=label_font)

    return img


def draw_section_table(title, subtitle, headers, cols, rows, *, row_height=48, value_cols=None, align_last_right=False):
    if value_cols is None:
        value_cols = len(headers)
    table_head = font(16, bold=True)
    table_body = font(13)
    table_small = font(12)
    table_bold = font(13, bold=True)
    subtitle_font = font(12)

    header_h = 40
    pad = 10
    sub_lines = wrap_text(subtitle, subtitle_font, W - MARGIN * 2) if subtitle else []
    table_top = 48 + len(sub_lines) * 16 if subtitle else 48
    table_h = header_h + len(rows) * row_height
    height = table_top + table_h + 20

    img = Image.new("RGB", (W, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((MARGIN, 14), title, fill=COLORS["title"], font=table_head)
    for i, line in enumerate(sub_lines):
        draw.text((MARGIN, 38 + i * 16), line, fill=COLORS["subtitle"], font=subtitle_font)

    x0, y0 = MARGIN, table_top
    table_w = sum(cols) + pad * 2
    rounded_rect(draw, (x0, y0, x0 + table_w, y0 + table_h), 10, WHITE, COLORS["table_border"])

    cx = x0 + pad
    for ci, (header, cw) in enumerate(zip(headers, cols)):
        draw.rectangle((cx, y0, cx + cw, y0 + header_h), fill=COLORS["table_header"])
        hx = cx + cw - 10 - text_width(header, table_head) if ci == len(cols) - 1 and align_last_right else cx + 8
        draw.text((hx, y0 + 12), header, fill=WHITE, font=table_head)
        cx += cw

    for r, row in enumerate(rows):
        ry = y0 + header_h + r * row_height
        kind = row[-1] if len(row) > value_cols else "row"
        values = list(row[:value_cols])
        if kind == "group":
            fill, fnt = "#e2e8f0", table_bold
        elif kind == "total":
            fill, fnt = "#dbeafe", table_bold
        else:
            fill = COLORS["table_row_a"] if r % 2 == 0 else COLORS["table_row_b"]
            fnt = table_body
        draw.rectangle((x0 + 1, ry, x0 + table_w - 1, ry + row_height), fill=fill)
        draw.line((x0, ry + row_height, x0 + table_w, ry + row_height), fill=COLORS["table_border"], width=1)
        cx = x0 + pad
        last = len(cols) - 1
        fonts_use = [fnt] * len(cols)
        if value_cols >= 3:
            fonts_use = [fnt, table_small if kind == "row" else fnt, fnt]
        if value_cols == 4:
            fonts_use = [fnt, table_small if kind == "row" else fnt, table_small if kind == "row" else fnt, fnt]
        for ci, (cw, text, fnt_use) in enumerate(zip(cols, values, fonts_use)):
            lines = wrap_text(str(text), fnt_use, cw - 16)[:3]
            ty = ry + max(6, (row_height - len(lines) * 15) // 2)
            for line in lines:
                tx = cx + cw - 10 - text_width(line, fnt_use) if ci == last and align_last_right else cx + 8
                draw.text((tx, ty), line, fill=COLORS["title"], font=fnt_use)
                ty += 15
            cx += cw
    return img


def compose():
    diagram = draw_diagram()
    piezas = draw_section_table(
        "Piezas — qué es, dónde y por qué",
        "Misma pila de voz que propuesta 1. Entrada PSTN en lugar de Meta WhatsApp.",
        ["Pieza", "Dónde", "Qué es", "Por qué"],
        [250, 170, 360, 360],
        [(*row, "row") for row in PIEZAS],
        row_height=50,
        value_cols=4,
    )
    c15 = draw_section_table(
        "Costos mensuales — 15 operadores",
        "100 % incidencias por llamada · 6 min · ≈ 4.000 min/mes · sin impuestos ni desarrollo",
        ["Concepto", "Detalle", "US$ / mes"],
        [280, 560, 110],
        COSTOS_15,
        row_height=40,
        align_last_right=True,
    )
    c1400 = draw_section_table(
        "Costos mensuales — 1.400 operadores",
        "≈ 370.000 min/mes · detalle en propuesta-4/costos.md",
        ["Concepto", "Detalle", "US$ / mes"],
        [280, 560, 110],
        COSTOS_1400,
        row_height=40,
        align_last_right=True,
    )

    gap = 28
    total_h = diagram.height + gap + piezas.height + gap + c15.height + gap + c1400.height
    out = Image.new("RGB", (W, total_h), BG)
    y = 0
    for part in (diagram, piezas, c15, c1400):
        out.paste(part, (0, y))
        y += part.height + gap

    diagram.save(OUT_DIAGRAM, "PNG", optimize=True)
    out.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({out.size[0]}x{out.size[1]})")
    print(f"Wrote {OUT_DIAGRAM} ({diagram.size[0]}x{diagram.size[1]})")


if __name__ == "__main__":
    compose()
