#!/usr/bin/env python3
"""Genera propuesta-5/arquitectura.png (PSTN + voz/IA on-premise)."""

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
    ("Celular del operador", "Campo", "Marca el número de soporte (PSTN).", "Sin WhatsApp ni datos en el piloto."),
    ("Proveedor PSTN", "Nube", "DID + minutos + SIP hacia el datacenter.", "Entrada teléfono normal; no se hospeda el carrier."),
    ("Reverse proxy / firewall", "On-premise (DMZ)", "SIP (y HTTPS consola) hacia adentro.", "Solo se publica lo del trunk."),
    ("LiveKit (open source)", "On-premise", "SIP, salas, ruido, despacho al agente.", "Sustituye LiveKit Cloud."),
    ("voice-agent", "On-premise", "Orquesta STT, LLM, YAML, TTS, DTMF.", "Misma pieza que P2; sin Fargate."),
    ("Motor YAML", "On-premise", "Tres árboles. LLM no redacta el paso.", "Determinismo del procedimiento."),
    ("Faster-Whisper", "On-premise, GPU", "Voz a texto en streaming.", "Sustituye Deepgram."),
    ("LLM chico", "On-premise, CPU", "Sí / no / persona.", "No hace falta GPU para clasificar."),
    ("Piper (TTS)", "On-premise, CPU", "Voz del agente; pasos fijos en MinIO.", "Sustituye Cartesia."),
    ("Redis + Postgres + MinIO", "On-premise", "Sesión, casos, audios.", "Los datos del caso no salen."),
    ("Consola de casos", "On-premise", "Bandeja mesa; botón tel:+57…", "Sin Cognito; sin bandeja WhatsApp."),
    ("SMS / correo", "PSTN o local", "Número de caso al escalar.", "Sustituye mensaje WhatsApp."),
]

COSTOS_15 = [
    ("On-premise", "", "≈ 215", "group"),
    ("1 servidor GPU", "T4 / L4 / RTX, amortizado 36 meses", "50", "row"),
    ("1 servidor CPU", "LiveKit, voice-agent, Postgres, Redis, MinIO, consola", "55", "row"),
    ("Energía y rack", "Si ya hay datacenter, sobre todo energía", "40", "row"),
    ("Respaldo y recambio", "Discos, snapshots", "20", "row"),
    ("Mantenimiento software", "Parches LiveKit, modelos, SO", "50", "row"),
    ("Telefonía PSTN", "", "≈ 15", "group"),
    ("DID + minutos entrantes", "≈ 4.000 min inbound (100 % llamadas)", "15", "row"),
    ("SMS (opcional)", "Número de caso al escalar", "10", "row"),
    ("Total 15 operadores", "vs ≈ 310 P4 nube  ·  vs ≈ 220 P2 WhatsApp", "≈ 240", "total"),
]

COSTOS_1400 = [
    ("On-premise", "", "≈ 1.500", "group"),
    ("6–8 GPU T4 (o 4 L4)", "Pico ≈ 40–50 llamadas; amortizado 36 meses", "550", "row"),
    ("3 servidores CPU", "LiveKit, apps, Postgres / Redis / MinIO", "180", "row"),
    ("Energía", "GPUs + CPU, 24×7", "280", "row"),
    ("Red, backup, recambio", "", "140", "row"),
    ("Mantenimiento software", "", "350", "row"),
    ("Telefonía PSTN", "", "≈ 450", "group"),
    ("DID + minutos entrantes", "≈ 370.000 min; tarifa negociable", "450", "row"),
    ("SMS", "Escalamientos", "80", "row"),
    ("Total 1.400 operadores", "vs ≈ 4.800 P4  ·  vs ≈ 1.800 P2", "≈ 2.030", "total"),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
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

    pstn = {"bg": COLORS["pstn_bg"], "border": COLORS["pstn_border"], "text": COLORS["pstn_text"]}
    onp = {"bg": WHITE, "border": COLORS["onp_border"], "text": COLORS["onp_text"]}
    gpu = {"bg": COLORS["gpu_bg"], "border": COLORS["gpu_border"], "text": COLORS["gpu_text"]}
    data = {"bg": COLORS["data_bg"], "border": COLORS["data_border"], "text": COLORS["data_text"]}
    app = {"bg": COLORS["app_bg"], "border": COLORS["app_border"], "text": COLORS["app_text"]}
    mesa = {"bg": COLORS["onp_bg"], "border": COLORS["onp_border"], "text": COLORS["onp_text"]}

    H = 1180
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw.text((MARGIN, 22), "Propuesta 5 — PSTN + voz e IA on-premise (P4 canal × P2 hosting)", fill=COLORS["title"], font=title_font)
    draw.text(
        (MARGIN, 58),
        "Sin WhatsApp  ·  operador marca número  ·  Whisper/Piper/LiveKit OSS en datacenter",
        fill=COLORS["subtitle"],
        font=subtitle_font,
    )

    op_w = 560
    op_x = (W - op_w) // 2
    op = draw_box(
        draw, op_x, 92, op_w,
        "1. Operador en el puesto (campo)",
        ["Marca el número de soporte desde el celular"],
        {"bg": WHITE, "border": "#94a3b8", "text": COLORS["title"]},
        box_title, box_body,
    )

    region_y = op[3] + 44
    nube_x, nube_w = MARGIN, 380
    gap = 24
    onp_x = nube_x + nube_w + gap
    onp_w = W - MARGIN - onp_x
    region_h = 980
    draw_region(draw, nube_x, region_y, nube_w, region_h, "NUBE  —  solo telefonía", COLORS["pstn_bg"], COLORS["pstn_border"], COLORS["pstn_text"], lane_font)
    draw_region(draw, onp_x, region_y, onp_w, region_h, "ON-PREMISE  —  datacenter  ·  aquí se convierte a texto y se decide", COLORS["onp_bg"], COLORS["onp_border"], COLORS["onp_text"], lane_font)

    inner = 16
    carrier = draw_box(
        draw, nube_x + inner, region_y + 50, nube_w - inner * 2,
        "2. Proveedor PSTN",
        ["Número DID Colombia", "Minutos entrantes", "SIP trunk → datacenter", "No interpreta ni guarda el caso"],
        pstn, box_title, box_body,
    )
    bus_y = op[3] + 16
    carrier_cx = nube_x + nube_w // 2
    draw.line((W // 2, op[3], W // 2, bus_y), fill=COLORS["arrow"], width=2)
    draw.line((W // 2, bus_y, carrier_cx, bus_y), fill=COLORS["arrow"], width=2)
    arrow_down(draw, carrier_cx, bus_y, carrier[1])

    draw.text((nube_x + inner, carrier[3] + 14), "Por qué nube", fill=COLORS["pstn_text"], font=box_title)
    why = wrap_text(
        "El carrier entrega el DID y el SIP. Meta/WhatsApp no entran. El procedimiento y el audio procesado viven on-premise.",
        box_body, nube_w - inner * 2,
    )
    ty = carrier[3] + 36
    for line in why:
        draw.text((nube_x + inner, ty), line, fill=COLORS["pstn_text"], font=box_body)
        ty += 16

    draw_box(
        draw, nube_x + inner, ty + 16, nube_w - inner * 2,
        "Sin Meta · sin LiveKit Cloud",
        ["Deepgram y Cartesia tampoco.", "Whisper, Piper y LiveKit OSS", "corren en el datacenter.", "Escalamiento: SMS + devolución PSTN."],
        pstn, box_title, box_body,
    )

    ox = onp_x + inner
    ow = onp_w - inner * 2
    cx = ox + ow // 2
    y = region_y + 50

    proxy = draw_box(draw, ox, y, ow, "3. Reverse proxy / firewall (DMZ)", ["SIP desde el proveedor PSTN. El resto no se publica."], onp, box_title, box_body)
    arrow_right(draw, carrier[2], (carrier[1] + carrier[3]) // 2, ox)
    arrow_down(draw, cx, proxy[3], proxy[3] + 26)

    y = proxy[3] + 26
    lk = draw_box(
        draw, ox, y, ow,
        "4. LiveKit OSS — solo audio",
        ["Termina el SIP, abre la sala, mezcla y cancela ruido. No convierte a texto ni clasifica."],
        gpu, box_title, box_body,
    )
    arrow_down(draw, cx, lk[3], lk[3] + 26)

    y = lk[3] + 26
    col_w = (ow - 14) // 2
    va = draw_box(
        draw, ox, y, col_w,
        "5. voice-agent (Python)",
        ["Proceso vuestro en la sala.", "Pide STT, LLM, YAML y TTS."],
        gpu, box_title, box_body,
    )
    stt = draw_box(
        draw, ox + col_w + 14, y, col_w,
        "6. Faster-Whisper (GPU)",
        ["Audio → texto, streaming.", "Cédula enmascarada."],
        gpu, box_title, box_body,
    )
    row1 = max(va[3], stt[3])
    arrow_down(draw, ox + col_w // 2, va[3], row1 + 26)
    arrow_down(draw, ox + col_w + 14 + col_w // 2, stt[3], row1 + 26)

    y = row1 + 26
    llm = draw_box(
        draw, ox, y, col_w,
        "7. LLM chico (CPU)",
        ["Etiqueta: sí / no /", "no_entendí / persona."],
        app, box_title, box_body,
    )
    yaml = draw_box(
        draw, ox + col_w + 14, y, col_w,
        "8. Motor YAML + Redis",
        ["Siguiente id de paso.", "Tres flujos deterministas."],
        app, box_title, box_body,
    )
    row2 = max(llm[3], yaml[3])
    arrow_down(draw, cx, row2, row2 + 26)

    y = row2 + 26
    minio = draw_box(draw, ox, y, col_w, "9a. MinIO — audio fijo", ["Id del YAML = archivo grabado."], data, box_title, box_body)
    piper = draw_box(draw, ox + col_w + 14, y, col_w, "9b. Piper CPU — frase suelta", ["Número de caso, nombre de puesto."], data, box_title, box_body)
    row9 = max(minio[3], piper[3])

    draw.text((ox, row9 + 18), "Audio de vuelta: Piper/MinIO → voice-agent → LiveKit → PSTN → operador", fill=COLORS["subtitle"], font=label_font)

    y = row9 + 42
    pg = draw_box(
        draw, ox, y, col_w,
        "10. Si escala → Postgres",
        ["Caso, pasos intentados,", "transcripción enmascarada."],
        data, box_title, box_body,
    )
    cons = draw_box(
        draw, ox + col_w + 14, y, col_w,
        "Consola + SMS / tel:+57",
        ["Sin transferencia en vivo.", "La mesa llama de vuelta por PSTN."],
        mesa, box_title, box_body,
    )
    arrow_down(draw, cx, row9 + 36, pg[1])

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
        "Canal PSTN (P4) + stack on-premise (P2). GPU solo en Faster-Whisper. El carrier es el único servicio de nube obligatorio.",
        ["Pieza", "Dónde", "Qué es", "Por qué"],
        [250, 170, 360, 360],
        [(*row, "row") for row in PIEZAS],
        row_height=50,
        value_cols=4,
    )
    c15 = draw_section_table(
        "Costos mensuales — 15 operadores",
        "100 % llamada · amortización 36 meses · sin impuestos ni sueldo de operación · vs ≈ 310 P4 / ≈ 220 P2",
        ["Concepto", "Detalle", "US$ / mes"],
        [280, 560, 110],
        COSTOS_15,
        row_height=40,
        align_last_right=True,
    )
    c1400 = draw_section_table(
        "Costos mensuales — 1.400 operadores",
        "≈ 370.000 min/mes · detalle en propuesta-5/costos.md · vs ≈ 4.800 P4 / ≈ 1.800 P2",
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
