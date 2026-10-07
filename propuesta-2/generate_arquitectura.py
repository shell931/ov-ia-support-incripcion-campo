#!/usr/bin/env python3
"""Genera propuesta-2/arquitectura.png (diagrama nube vs on-premise + piezas + costos)."""

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
    "onp_bg": "#f0fdf4",
    "onp_border": "#16a34a",
    "onp_text": "#14532d",
    "gpu_bg": "#fff7ed",
    "gpu_border": "#ea580c",
    "gpu_text": "#9a3412",
    "data_bg": "#f5f3ff",
    "data_border": "#7c3aed",
    "data_text": "#4c1d95",
    "app_bg": "#eef2ff",
    "app_border": "#4f46e5",
    "app_text": "#312e81",
    "arrow": "#64748b",
    "table_header": "#1e293b",
    "table_row_a": "#ffffff",
    "table_row_b": "#f1f5f9",
    "table_border": "#cbd5e1",
}

PIEZAS = [
    ("Celular del operador", "Campo", "WhatsApp: chat o llamada.", "La tableta del puesto es lo que falla."),
    ("Meta WhatsApp Cloud API", "Nube", "Webhook de chat y SIP de la llamada.", "WhatsApp no se hospeda."),
    ("Reverse proxy / firewall", "On-premise (DMZ)", "HTTPS y SIP desde Meta hacia adentro.", "Solo se publica lo que Meta necesita."),
    ("LiveKit (open source)", "On-premise", "SIP, salas, ruido, despacho al agente.", "Sustituye LiveKit Cloud y el cobro por minuto."),
    ("gateway + cola + worker", "On-premise", "Chat: webhook 200, cola, casos.", "Igual que la propuesta 1, sin SQS de AWS."),
    ("voice-agent", "On-premise", "Orquesta la llamada: escucha, clasifica, habla.", "Misma pieza; ya no corre en Fargate."),
    ("Motor YAML", "On-premise", "Tres árboles. LLM no redacta el paso.", "Un flujo para chat y voz."),
    ("Faster-Whisper", "On-premise, GPU", "Voz a texto en streaming.", "Sustituye Deepgram. GPU solo aquí."),
    ("LLM chico", "On-premise, CPU", "Sí / no / persona.", "No hace falta GPU para clasificar."),
    ("Piper (TTS)", "On-premise, CPU", "Voz del agente; pasos fijos en MinIO.", "Sustituye Cartesia."),
    ("Redis + Postgres + MinIO", "On-premise", "Sesión, casos, audios y fotos.", "Los datos del caso no salen del datacenter."),
    ("Consola de casos", "On-premise", "Bandeja de la mesa, login local.", "Sin Cognito ni CloudFront."),
]

COSTOS_15 = [
    ("On-premise", "", "≈ 215", "group"),
    ("1 servidor GPU", "T4 / L4 / RTX, amortizado 36 meses", "50", "row"),
    ("1 servidor CPU", "LiveKit, apps, Postgres, Redis, MinIO, consola", "55", "row"),
    ("Energía y rack", "Si ya hay datacenter, sobre todo energía", "40", "row"),
    ("Respaldo y recambio", "Discos, snapshots", "20", "row"),
    ("Mantenimiento software", "Parches LiveKit, modelos, SO", "50", "row"),
    ("WhatsApp (nube)", "", "≈ 3", "group"),
    ("Llamadas WhatsApp", "Iniciadas por el operador; sin costo empresa", "0", "row"),
    ("Mensajes WhatsApp", "1.000 gratis; luego 0,0008 en Colombia", "3", "row"),
    ("Total 15 operadores", "≈ COP 0,7 millón a 3.340 COP/US$  ·  vs ≈ 300 en nube", "≈ 220", "total"),
]

COSTOS_1400 = [
    ("On-premise", "", "≈ 1.500", "group"),
    ("6–8 GPU T4 (o 4 L4)", "Pico ≈ 40–50 llamadas; amortizado 36 meses", "550", "row"),
    ("3 servidores CPU", "LiveKit, apps, Postgres / Redis / MinIO", "180", "row"),
    ("Energía", "GPUs + CPU, 24×7", "280", "row"),
    ("Red, backup, recambio", "", "140", "row"),
    ("Mantenimiento software", "", "350", "row"),
    ("WhatsApp (nube)", "", "≈ 295", "group"),
    ("Llamadas WhatsApp", "Iniciadas por el operador; sin costo empresa", "0", "row"),
    ("Mensajes WhatsApp", "≈ 369.000 × 0,0008", "295", "row"),
    ("Total 1.400 operadores", "≈ COP 6 millones  ·  vs ≈ 4.600 en nube", "≈ 1.800", "total"),
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


def draw_region(draw, x, y, w, h, title, bg, border, text_color, lane_font):
    rounded_rect(draw, (x, y, x + w, y + h), 16, bg, border, 2)
    draw.text((x + 16, y + 12), title, fill=text_color, font=lane_font)


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
    lane_font = font(15, bold=True)
    box_title = font(14, bold=True)
    box_body = font(12)
    label_font = font(12)

    nube = {"bg": COLORS["nube_bg"], "border": COLORS["nube_border"], "text": COLORS["nube_text"]}
    onp = {"bg": WHITE, "border": COLORS["onp_border"], "text": COLORS["onp_text"]}
    gpu = {"bg": COLORS["gpu_bg"], "border": COLORS["gpu_border"], "text": COLORS["gpu_text"]}
    data = {"bg": COLORS["data_bg"], "border": COLORS["data_border"], "text": COLORS["data_text"]}
    app = {"bg": COLORS["app_bg"], "border": COLORS["app_border"], "text": COLORS["app_text"]}
    mesa = {"bg": COLORS["onp_bg"], "border": COLORS["onp_border"], "text": COLORS["onp_text"]}

    H = 1180
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw.text((MARGIN, 22), "Propuesta 2 — voz e IA on-premise", fill=COLORS["title"], font=title_font)
    draw.text(
        (MARGIN, 58),
        "Mismo WhatsApp y mismo árbol YAML  ·  Meta en la nube  ·  STT, TTS, LLM y datos en el datacenter",
        fill=COLORS["subtitle"],
        font=subtitle_font,
    )

    op_w, op_h_box = 560, 0
    op_x = (W - op_w) // 2
    op = draw_box(
        draw, op_x, 96, op_w,
        "Operador en el puesto (campo)",
        ["WhatsApp en el celular: mensaje o llamada de voz"],
        {"bg": WHITE, "border": "#94a3b8", "text": COLORS["title"]},
        box_title, box_body,
    )

    region_y = op[3] + 48
    nube_x, nube_w = MARGIN, 400
    gap = 28
    onp_x = nube_x + nube_w + gap
    onp_w = W - MARGIN - onp_x
    region_h = 860
    draw_region(draw, nube_x, region_y, nube_w, region_h, "NUBE  —  solo el canal", COLORS["nube_bg"], COLORS["nube_border"], COLORS["nube_text"], lane_font)
    draw_region(draw, onp_x, region_y, onp_w, region_h, "ON-PREMISE  —  datacenter del cliente", COLORS["onp_bg"], COLORS["onp_border"], COLORS["onp_text"], lane_font)

    inner = 18
    meta = draw_box(
        draw, nube_x + inner, region_y + 52, nube_w - inner * 2,
        "Meta WhatsApp Cloud API",
        ["Chat: webhook HTTPS", "Voz: llamada SIP", "No interpreta ni guarda el caso"],
        nube, box_title, box_body,
    )
    # Operador → Meta (el canal siempre pasa por la nube)
    bus_y = op[3] + 18
    meta_cx = nube_x + nube_w // 2
    draw.line((W // 2, op[3], W // 2, bus_y), fill=COLORS["arrow"], width=2)
    draw.line((W // 2, bus_y, meta_cx, bus_y), fill=COLORS["arrow"], width=2)
    arrow_down(draw, meta_cx, bus_y, meta[1])
    draw.text((nube_x + inner, meta[3] + 16), "Por qué nube", fill=COLORS["nube_text"], font=box_title)
    why_nube = wrap_text(
        "WhatsApp no se instala en el datacenter. Meta solo entrega el mensaje o el audio. El procedimiento y los datos del caso no viven aquí.",
        box_body, nube_w - inner * 2,
    )
    ty = meta[3] + 38
    for line in why_nube:
        draw.text((nube_x + inner, ty), line, fill=COLORS["nube_text"], font=box_body)
        ty += 16

    dmz = draw_box(
        draw, nube_x + inner, ty + 20, nube_w - inner * 2,
        "Llega al datacenter por",
        ["HTTPS (chat) y SIP (voz)", "hacia el reverse proxy / DMZ"],
        nube, box_title, box_body,
    )

    ox = onp_x + inner
    ow = onp_w - inner * 2
    y = region_y + 52
    proxy = draw_box(draw, ox, y, ow, "Reverse proxy / firewall (DMZ)", ["Punto de entrada desde Meta. El resto de servicios no se publican."], onp, box_title, box_body)
    arrow_right(draw, meta[2], (meta[1] + meta[3]) // 2, ox)
    arrow_down(draw, ox + ow // 2, proxy[3], proxy[3] + 28)

    y = proxy[3] + 28
    col_w = (ow - 16) // 2
    chat = draw_box(draw, ox, y, col_w, "Chat", ["gateway → cola → worker", "Motor YAML + LLM CPU"], app, box_title, box_body)
    voice = draw_box(draw, ox + col_w + 16, y, col_w, "Voz", ["LiveKit OSS → voice-agent", "Whisper GPU → YAML → Piper CPU"], gpu, box_title, box_body)
    row_h = max(chat[3], voice[3])
    arrow_down(draw, ox + ow // 2, row_h, row_h + 28)

    y = row_h + 28
    motor = draw_box(
        draw, ox, y, ow,
        "Motor de flujos (YAML) — on-premise",
        ["Mismo árbol que chat y voz: logueo, tableta sin internet, tableta dañada.", "El LLM solo marca sí / no / persona. El id del paso elige el audio en MinIO o el texto de WhatsApp."],
        app, box_title, box_body,
    )
    arrow_down(draw, ox + ow // 2, motor[3], motor[3] + 28)

    y = motor[3] + 28
    dw = (ow - 32) // 3
    d1 = draw_box(draw, ox, y, dw, "Redis", ["Sesión: paso e intentos"], data, box_title, box_body)
    d2 = draw_box(draw, ox + dw + 16, y, dw, "Postgres", ["Casos e historial"], data, box_title, box_body)
    d3 = draw_box(draw, ox + (dw + 16) * 2, y, dw, "MinIO", ["Audios de pasos y fotos"], data, box_title, box_body)
    data_bottom = max(d1[3], d2[3], d3[3])
    arrow_down(draw, ox + ow // 2, data_bottom, data_bottom + 28)

    y = data_bottom + 28
    cons = draw_box(
        draw, ox, y, ow,
        "Consola de la mesa + correo local",
        ["Cola de casos, toma, transcripción enmascarada. Sin transferencia en vivo: la mesa llama de vuelta por WhatsApp."],
        mesa, box_title, box_body,
    )

    draw.text((ox, cons[3] + 14), "GPU solo en Whisper. Clasificador y Piper en CPU. Meta sigue viendo el audio de WhatsApp; el caso no sale.", fill=COLORS["subtitle"], font=label_font)

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
    table_top = 64 if subtitle else 48
    # extra lines of subtitle
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
        "GPU solo en Faster-Whisper. Meta es el único servicio de nube obligatorio.",
        ["Pieza", "Dónde", "Qué es", "Por qué"],
        [250, 170, 360, 360],
        [(*row, "row") for row in PIEZAS],
        row_height=50,
        value_cols=4,
    )
    c15 = draw_section_table(
        "Costos mensuales — 15 operadores",
        "Amortización a 36 meses · sin impuestos ni sueldo de operación · vs ≈ 300 US$ en la propuesta 1 (nube)",
        ["Concepto", "Detalle", "US$ / mes"],
        [280, 560, 110],
        COSTOS_15,
        row_height=40,
        align_last_right=True,
    )
    c1400 = draw_section_table(
        "Costos mensuales — 1.400 operadores",
        "Mismos supuestos de uso que docs/costos.md · vs ≈ 4.600 US$ en la propuesta 1 (nube)",
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
