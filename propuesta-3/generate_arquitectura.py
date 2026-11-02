#!/usr/bin/env python3
"""Genera propuesta-3/arquitectura.png (diagrama + piezas + costos)."""

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
    "nube_bg": "#eff6ff",
    "nube_border": "#2563eb",
    "nube_text": "#1e3a8a",
    "rail_bg": "#eef2ff",
    "rail_border": "#4f46e5",
    "rail_text": "#312e81",
    "ai_bg": "#fff7ed",
    "ai_border": "#ea580c",
    "ai_text": "#9a3412",
    "data_bg": "#f5f3ff",
    "data_border": "#7c3aed",
    "data_text": "#4c1d95",
    "chat_bg": "#eff6ff",
    "chat_border": "#3b82f6",
    "voice_bg": "#fdf2f8",
    "voice_border": "#db2777",
    "voice_text": "#831843",
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
    ("Celular del operador", "Campo", "WhatsApp: escribe o llama.", "La tableta del puesto es lo que falla."),
    ("Meta WhatsApp Cloud API", "Nube", "Webhook de chat y SIP de llamada.", "WhatsApp no se hospeda; canal obligatorio."),
    ("Railway (API + worker)", "PaaS", "Webhook 200, cola, motor YAML, sideband Realtime, API consola.", "Menos piezas que ECS + SQS + Terraform en piloto."),
    ("Motor YAML", "Railway (código)", "Tres árboles; el LLM no redacta el paso.", "Mismo flujo en chat y voz."),
    ("Claude Haiku", "Anthropic API", "Texto → sí / no / no_entendí / persona.", "Barato y rápido; cerebro de clasificación."),
    ("GPT Live / OpenAI Realtime", "OpenAI", "En llamada: escucha y habla; sideband con Railway.", "Sustituye LiveKit + Deepgram + Cartesia en voz."),
    ("Supabase Postgres", "Supabase", "Casos, sesión por teléfono, historial enmascarado.", "RDS administrado; RLS para mesa y Censo."),
    ("Supabase Storage", "Supabase", "Fotos WhatsApp y audios fijos de pasos.", "Equivalente a S3/MinIO en piloto."),
    ("Supabase Auth", "Supabase", "Login de la consola de mesa.", "Sustituye Cognito en piloto."),
    ("Consola web", "Railway o Vercel", "Cola, tomar caso, wa.me para devolver llamada.", "Misma mesa que otras propuestas."),
    ("Puente SIP (plan B)", "Opcional", "Solo si Meta no termina SIP en OpenAI.", "LiveKit OSS mínimo; la lógica sigue en Railway."),
]

COSTOS_15 = [
    ("Stack gestionado", "", "≈ 60", "group"),
    ("Railway", "API, worker, despliegues", "30", "row"),
    ("Supabase Pro", "Postgres, Storage, Auth", "30", "row"),
    ("IA y voz", "", "≈ 125", "group"),
    ("Claude Haiku", "Chat + clasificación en llamada", "10", "row"),
    ("OpenAI Realtime", "≈ 2.000 min de voz al mes", "115", "row"),
    ("WhatsApp (nube)", "", "≈ 3", "group"),
    ("Llamadas WhatsApp", "Iniciadas por el operador; sin costo empresa", "0", "row"),
    ("Mensajes WhatsApp", "1.000 gratis; luego 0,0008 en Colombia", "3", "row"),
    ("Total 15 operadores", "≈ COP 0,6 millón a 3.340 COP/US$  ·  vs ≈ 300 propuesta 1", "≈ 190", "total"),
]

COSTOS_1400 = [
    ("Stack gestionado", "", "≈ 280", "group"),
    ("Railway", "Más CPU/RAM y réplicas en pico", "120", "row"),
    ("Supabase", "Plan team, más storage y conexiones", "160", "row"),
    ("IA y voz", "", "≈ 3.500", "group"),
    ("Claude Haiku", "≈ 840.000 clasificaciones", "90", "row"),
    ("OpenAI Realtime", "≈ 185.000 min; tarifa lista OpenAI", "3.400", "row"),
    ("WhatsApp (nube)", "", "≈ 295", "group"),
    ("Llamadas WhatsApp", "Iniciadas por el operador; sin costo empresa", "0", "row"),
    ("Mensajes WhatsApp", "≈ 369.000 × 0,0008", "295", "row"),
    ("Total 1.400 operadores", "Revisar minuto Realtime  ·  vs ≈ 4.600 propuesta 1", "≈ 4.100", "total"),
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


def arrow_right(draw, x1, y, x2):
    if x2 - x1 < 14:
        return
    draw.line((x1, y, x2 - 10, y), fill=COLORS["arrow"], width=2)
    draw.polygon([(x2, y), (x2 - 10, y - 6), (x2 - 10, y + 6)], fill=COLORS["arrow"])


def draw_diagram():
    title_font = font(26, bold=True)
    subtitle_font = font(14)
    box_title = font(14, bold=True)
    box_body = font(12)
    label_font = font(12)

    nube = {"bg": COLORS["nube_bg"], "border": COLORS["nube_border"], "text": COLORS["nube_text"]}
    rail = {"bg": COLORS["rail_bg"], "border": COLORS["rail_border"], "text": COLORS["rail_text"]}
    ai = {"bg": COLORS["ai_bg"], "border": COLORS["ai_border"], "text": COLORS["ai_text"]}
    chat = {"bg": COLORS["chat_bg"], "border": COLORS["chat_border"], "text": COLORS["nube_text"]}
    voice = {"bg": COLORS["voice_bg"], "border": COLORS["voice_border"], "text": COLORS["voice_text"]}
    data = {"bg": COLORS["data_bg"], "border": COLORS["data_border"], "text": COLORS["data_text"]}
    mesa = {"bg": COLORS["mesa_bg"], "border": COLORS["mesa_border"], "text": COLORS["mesa_text"]}

    H = 1180
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw.text((MARGIN, 22), "Propuesta 3 — WhatsApp + Railway + Supabase + Haiku + GPT Live", fill=COLORS["title"], font=title_font)
    draw.text(
        (MARGIN, 58),
        "Haiku y YAML deciden el paso  ·  GPT Live solo habla en la llamada  ·  chat y voz comparten Supabase",
        fill=COLORS["subtitle"],
        font=subtitle_font,
    )

    op_w = 520
    op_x = (W - op_w) // 2
    op = draw_box(
        draw, op_x, 92, op_w,
        "1. Operador (campo)",
        ["WhatsApp: mensaje o llamada al número de soporte"],
        {"bg": WHITE, "border": "#94a3b8", "text": COLORS["title"]},
        box_title, box_body,
    )

    meta_w = 720
    meta_x = (W - meta_w) // 2
    meta = draw_box(
        draw, meta_x, op[3] + 36, meta_w,
        "2. Meta WhatsApp Cloud API (nube)",
        ["Chat → webhook HTTPS a Railway", "Llamada → SIP (WhatsApp Calling)", "No guarda el procedimiento"],
        nube, box_title, box_body,
    )
    arrow_down(draw, W // 2, op[3], meta[1])

    y = meta[3] + 32
    col_w = (W - MARGIN * 2 - 20) // 2
    lx, rx = MARGIN, MARGIN + col_w + 20
    lcx, rcx = lx + col_w // 2, rx + col_w // 2

    draw.text((lx, y), "CHAT", fill=COLORS["chat_border"], font=font(13, bold=True))
    draw.text((rx, y), "VOZ", fill=COLORS["voice_border"], font=font(13, bold=True))
    y += 22

    wh = draw_box(
        draw, lx, y, col_w,
        "3a. Railway — webhook",
        ["Responde 200, encola,", "lee/escribe sesión en Supabase"],
        chat, box_title, box_body,
    )
    rt = draw_box(
        draw, rx, y, col_w,
        "3b. GPT Live / Realtime (OpenAI)",
        ["Meta SIP entra aquí (PoC).", "Audio bidireccional con el operador."],
        voice, box_title, box_body,
    )
    bus_y = meta[3] + 12
    draw.line((lcx, bus_y, lcx, wh[1]), fill=COLORS["arrow"], width=2)
    draw.line((rcx, bus_y, rcx, rt[1]), fill=COLORS["arrow"], width=2)
    draw.line((meta_x, bus_y, meta_x + meta_w, bus_y), fill=COLORS["arrow"], width=2)
    draw.line((meta_x, bus_y, lcx, bus_y), fill=COLORS["arrow"], width=2)
    draw.line((meta_x + meta_w, bus_y, rcx, bus_y), fill=COLORS["arrow"], width=2)

    y2 = max(wh[3], rt[3]) + 24
    hk_l = draw_box(draw, lx, y2, col_w, "4a. Claude Haiku", ["Clasifica el texto del operador"], ai, box_title, box_body)
    sb = draw_box(
        draw, rx, y2, col_w,
        "4b. Sideband → Railway",
        ["Cada turno: transcripción,", "Haiku, YAML, qué decir o qué audio"],
        rail, box_title, box_body,
    )
    arrow_down(draw, lcx, wh[3], hk_l[1])
    arrow_down(draw, rcx, rt[3], sb[1])
    arrow_right(draw, sb[0] - 8, (sb[1] + sb[3]) // 2, lx + col_w + 8)

    y3 = max(hk_l[3], sb[3]) + 24
    yaml = draw_box(
        draw, MARGIN, y3, W - MARGIN * 2,
        "5. Motor YAML (Railway)",
        ["Con sesión en Supabase elige el siguiente id: logueo, tableta sin internet, tableta dañada.", "El LLM no redacta; solo etiqueta."],
        rail, box_title, box_body,
    )
    arrow_down(draw, lcx, hk_l[3], yaml[1])
    arrow_down(draw, rcx, sb[3], yaml[1])

    y4 = yaml[3] + 24
    dw = (W - MARGIN * 2 - 14) // 2
    sb_data = draw_box(
        draw, MARGIN, y4, dw,
        "6. Supabase",
        ["Postgres: casos y sesión", "Storage: fotos y audios de pasos", "Auth: consola mesa"],
        data, box_title, box_body,
    )
    out = draw_box(
        draw, MARGIN + dw + 14, y4, dw,
        "7. Respuesta al operador",
        ["Chat: mensaje por Graph API", "Voz: Realtime habla (clip Storage o TTS)", "Si escala: número de caso por WhatsApp"],
        mesa, box_title, box_body,
    )
    arrow_down(draw, W // 2, yaml[3], sb_data[1])

    draw.text(
        (MARGIN, out[3] + 20),
        "Sin transferencia en vivo · la mesa devuelve la llamada por WhatsApp",
        fill=COLORS["subtitle"],
        font=label_font,
    )

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
        "Canal WhatsApp (Meta). Lógica y datos en Railway + Supabase. Voz en OpenAI Realtime; clasificación en Haiku.",
        ["Pieza", "Dónde", "Qué es", "Por qué"],
        [250, 170, 360, 360],
        [(*row, "row") for row in PIEZAS],
        row_height=50,
        value_cols=4,
    )
    c15 = draw_section_table(
        "Costos mensuales — 15 operadores",
        "22 días · 2 incid./día · 50 % chat / 50 % voz · 6 min/llamada · sin impuestos ni desarrollo",
        ["Concepto", "Detalle", "US$ / mes"],
        [280, 560, 110],
        COSTOS_15,
        row_height=40,
        align_last_right=True,
    )
    c1400 = draw_section_table(
        "Costos mensuales — 1.400 operadores",
        "Mismos supuestos que propuesta-1/costos.md · minuto Realtime según tarifa OpenAI al escalar",
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
