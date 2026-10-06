#!/usr/bin/env python3
"""Genera docs/diagramas/infraestructura.png (diagrama + tabla Piezas)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "infraestructura.png"
OUT_DIAGRAM = ROOT / "infraestructura-diagrama.png"

W = 1480
MARGIN = 40
BG = "#f8fafc"
WHITE = "#ffffff"

COLORS = {
    "title": "#0f172a",
    "subtitle": "#475569",
    "step": "#2563eb",
    "step_text": "#ffffff",
    "chat_bg": "#eff6ff",
    "chat_border": "#3b82f6",
    "chat_text": "#1e3a8a",
    "voice_bg": "#fdf2f8",
    "voice_border": "#db2777",
    "voice_text": "#831843",
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
    ("gateway (ECS Fargate)", "Recibe webhook de WhatsApp, responde 200 y encola en SQS. API de la consola.", "Meta reintenta si el webhook tarda; procesamiento aparte."),
    ("worker (ECS Fargate)", "Conversación WhatsApp: motor de flujos, LLM, respuestas y casos.", "Escala con la cola, no con HTTP."),
    ("voice-agent (ECS Fargate)", "LiveKit Agents: escucha, interpreta, habla, teclado y caso por llamada.", "WebSocket saliente a LiveKit; sin IP pública."),
    ("Motor de flujos", "Librería compartida. Lee YAML de los tres casos.", "Un árbol para chat y voz."),
    ("LiveKit Cloud", "SIP de WhatsApp, mezcla audio, cancela ruido, despacha al agente.", "Sin operar SIP propio en el piloto."),
    ("ElastiCache Redis", "Sesión por teléfono: caso, paso, intentos.", "Retomar chat/voz si se corta."),
    ("RDS Postgres", "Casos, historial enmascarado, flujos, métricas.", "Una base para agente y consola."),
    ("S3", "Fotos WhatsApp y audio presintetizado de pasos.", "Pasos fijos sin latencia de TTS."),
    ("CloudFront + Cognito", "Consola web de la mesa con login por persona.", "Bandeja de casos sin herramienta previa."),
    ("SES", "Correo a mesa y Censo en casos altos.", "Aviso aunque nadie tenga la consola abierta."),
    ("Secrets Manager, CloudWatch", "Tokens de proveedores. Logs enmascarados y alarmas.", "—"),
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


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str,
    width: int = 2,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_step_badge(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    number: str,
    font: ImageFont.FreeTypeFont,
) -> None:
    x, y = center
    r = BADGE_R
    draw.ellipse((x - r - 2, y - r - 2, x + r + 2, y + r + 2), fill=BG)
    draw.ellipse((x - r, y - r, x + r, y + r), fill=COLORS["step"], outline=COLORS["step"])
    bbox = draw.textbbox((0, 0), number, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x - tw / 2, y - th / 2 - 1), number, fill=COLORS["step_text"], font=font)


def text_width(text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if text_width(trial, font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def draw_box(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    title: str,
    lines: list[str],
    style: dict[str, str],
    title_font: ImageFont.FreeTypeFont,
    body_font: ImageFont.FreeTypeFont,
    pad: int = 12,
) -> tuple[int, int, int, int]:
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(wrap_text(line, body_font, w - pad * 2))
    title_h = title_font.getbbox(title)[3] - title_font.getbbox(title)[1] + 6
    line_h = body_font.getbbox("Ag")[3] - body_font.getbbox("Ag")[1] + 4
    h = pad * 2 + title_h + len(wrapped) * line_h
    box = (x, y, x + w, y + h)
    rounded_rect(draw, box, 12, style["bg"], style["border"])
    draw.text((x + pad, y + pad), title, fill=style["text"], font=title_font)
    ty = y + pad + title_h
    for line in wrapped:
        draw.text((x + pad, ty), line, fill=style["text"], font=body_font)
        ty += line_h
    return box


V_GAP = 52
SECTION_GAP = 64
LANE_GAP = 56
BADGE_R = 16


def arrow_down(draw: ImageDraw.ImageDraw, x: int, y1: int, y2: int, gap: int = 10) -> None:
    y1 = y1 + gap
    y2 = y2 - gap
    if y2 <= y1 + 8:
        return
    draw.line((x, y1, x, y2 - 8), fill=COLORS["arrow"], width=2)
    draw.polygon([(x, y2), (x - 6, y2 - 10), (x + 6, y2 - 10)], fill=COLORS["arrow"])


def arrow_right(draw: ImageDraw.ImageDraw, x1: int, y: int, x2: int, gap: int = 10) -> None:
    x1 = x1 + gap
    x2 = x2 - gap
    if x2 <= x1 + 8:
        return
    draw.line((x1, y, x2 - 8, y), fill=COLORS["arrow"], width=2)
    draw.polygon([(x2, y), (x2 - 10, y - 6), (x2 - 10, y + 6)], fill=COLORS["arrow"])


def arrow_split_down(
    draw: ImageDraw.ImageDraw,
    top_x: int,
    top_y: int,
    left_x: int,
    right_x: int,
    bottom_y: int,
) -> None:
    """Una salida arriba que se divide hacia dos carriles."""
    mid_y = top_y + (bottom_y - top_y) // 2
    draw.line((top_x, top_y, top_x, mid_y), fill=COLORS["arrow"], width=2)
    draw.line((left_x, mid_y, right_x, mid_y), fill=COLORS["arrow"], width=2)
    arrow_down(draw, left_x, mid_y, bottom_y, gap=0)
    arrow_down(draw, right_x, mid_y, bottom_y, gap=0)


def arrow_merge_down(
    draw: ImageDraw.ImageDraw,
    left_x: int,
    right_x: int,
    top_y: int,
    bottom_x: int,
    bottom_y: int,
) -> None:
    """Dos carriles convergen hacia un punto central abajo."""
    mid_y = top_y + (bottom_y - top_y) // 2
    arrow_down(draw, left_x, top_y, mid_y, gap=10)
    arrow_down(draw, right_x, top_y, mid_y, gap=10)
    draw.line((left_x, mid_y, right_x, mid_y), fill=COLORS["arrow"], width=2)
    arrow_down(draw, bottom_x, mid_y, bottom_y, gap=0)


def arrow_left_dashed(draw: ImageDraw.ImageDraw, x1: int, y: int, x2: int, label: str, font) -> None:
    step = 12
    x = x1
    while x > x2 + 8:
        nx = max(x - step, x2 + 8)
        draw.line((x, y, nx, y), fill=COLORS["mesa_border"], width=2)
        x -= step * 2
    draw.polygon([(x2, y), (x2 + 10, y - 6), (x2 + 10, y + 6)], fill=COLORS["mesa_border"])
    tw = text_width(label, font)
    draw.text(((x1 + x2) // 2 - tw // 2, y - 22), label, fill=COLORS["mesa_text"], font=font)


def gap_center_y(box_a: tuple[int, int, int, int], box_b: tuple[int, int, int, int]) -> int:
    return (box_a[3] + box_b[1]) // 2


def draw_lane_title(draw, x, y, w, text, bg, border, text_color, font):
    rounded_rect(draw, (x, y, x + w, y + 34), 8, bg, border, 1)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) // 2, y + 8), text, fill=text_color, font=font)


def draw_diagram() -> Image.Image:
    title_font = font(28, bold=True)
    subtitle_font = font(15)
    lane_font = font(14, bold=True)
    step_font = font(14, bold=True)
    box_title = font(15, bold=True)
    box_body = font(13)
    label_font = font(12)

    chat_style = {"bg": COLORS["chat_bg"], "border": COLORS["chat_border"], "text": COLORS["chat_text"]}
    voice_style = {"bg": COLORS["voice_bg"], "border": COLORS["voice_border"], "text": COLORS["voice_text"]}
    aws_style = {"bg": COLORS["aws_bg"], "border": COLORS["aws_border"], "text": COLORS["aws_text"]}
    ai_style = {"bg": COLORS["ai_bg"], "border": COLORS["ai_border"], "text": COLORS["ai_text"]}
    data_style = {"bg": COLORS["data_bg"], "border": COLORS["data_border"], "text": COLORS["data_text"]}
    mesa_style = {"bg": COLORS["mesa_bg"], "border": COLORS["mesa_border"], "text": COLORS["mesa_text"]}

    chat_x, voice_x = MARGIN, W // 2 + 10
    lane_w = (W - MARGIN * 2 - 20) // 2
    chat_cx = chat_x + lane_w // 2
    voice_cx = voice_x + lane_w // 2
    inner_w = lane_w - 40

    # --- layout pass: compute Y positions ---
    y = 100
    op_x, op_w = MARGIN + 420, 520
    op_y = y
    y += 78 + SECTION_GAP

    lane_y = y
    y += 42 + LANE_GAP

    box_defs = [
        ("Meta WhatsApp Cloud API", ["Recibe mensaje del operador"], chat_style),
        ("WAF + ALB → gateway → SQS", ["Webhook rápido 200 · mensaje en cola"], aws_style),
        ("worker + motor de flujos", ["Clasifica con LLM · responde · crea caso si aplica"], aws_style),
    ]
    voice_defs = [
        ("Meta → LiveKit Cloud", ["Llamada SIP, salas, cancelación de ruido"], voice_style),
        ("voice-agent (LiveKit Agents)", ["Una sesión por llamada activa"], aws_style),
        ("Deepgram → LLM → Cartesia", ["Escucha · intención · habla · audio de pasos en S3"], ai_style),
    ]

    chat_ys: list[int] = []
    voice_ys: list[int] = []
    for _ in range(3):
        chat_ys.append(y)
        voice_ys.append(y)
        y += 72 + V_GAP

    data_title_y = y + SECTION_GAP - V_GAP
    data_boxes_y = data_title_y + 42 + LANE_GAP
    resp_y = data_boxes_y + 72 + SECTION_GAP
    esc_title_y = resp_y + 78 + SECTION_GAP
    esc_boxes_y = esc_title_y + 42 + LANE_GAP
    bottom_y = esc_boxes_y + 72 + 56

    H = bottom_y + MARGIN
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw.text((MARGIN, 24), "Infraestructura del piloto — flujo paso a paso", fill=COLORS["title"], font=title_font)
    draw.text(
        (MARGIN, 62),
        "WhatsApp único canal · chat y llamada · escalamiento sin transferencia en vivo",
        fill=COLORS["subtitle"],
        font=subtitle_font,
    )
    rounded_rect(draw, (W - 210, 24, W - MARGIN, 58), 8, COLORS["aws_bg"], COLORS["aws_border"], 1)
    draw.text((W - 198, 33), "AWS us-east-1 · VPC privada", fill=COLORS["aws_text"], font=label_font)

    # Step 1
    op_box = draw_box(
        draw, op_x, op_y, op_w,
        "Operador en puesto de inscripción",
        ["WhatsApp: mensajes de texto o llamada de voz"],
        {"bg": WHITE, "border": "#94a3b8", "text": COLORS["title"]},
        box_title, box_body,
    )
    draw_step_badge(draw, (W // 2, (op_box[3] + lane_y) // 2), "1", step_font)

    draw_lane_title(draw, chat_x, lane_y, lane_w, "Flujo chat (mensajes)", COLORS["chat_bg"], COLORS["chat_border"], COLORS["chat_text"], lane_font)
    draw_lane_title(draw, voice_x, lane_y, lane_w, "Flujo voz (llamada WhatsApp)", COLORS["voice_bg"], COLORS["voice_border"], COLORS["voice_text"], lane_font)

    arrow_split_down(draw, W // 2, op_box[3], chat_cx, voice_cx, chat_ys[0])

    chat_boxes: list[tuple[int, int, int, int]] = []
    voice_boxes: list[tuple[int, int, int, int]] = []
    for i, (title, lines, style) in enumerate(box_defs):
        chat_boxes.append(draw_box(draw, chat_x + 20, chat_ys[i], inner_w, title, lines, style, box_title, box_body))
    for i, (title, lines, style) in enumerate(voice_defs):
        voice_boxes.append(draw_box(draw, voice_x + 20, voice_ys[i], inner_w, title, lines, style, box_title, box_body))

    for i in range(2):
        cy = gap_center_y(chat_boxes[i], chat_boxes[i + 1])
        vy = gap_center_y(voice_boxes[i], voice_boxes[i + 1])
        draw_step_badge(draw, (chat_cx, cy), str(i + 3), step_font)
        draw_step_badge(draw, (voice_cx, vy), str(i + 3), step_font)
        arrow_down(draw, chat_cx, chat_boxes[i][3], chat_boxes[i + 1][1])
        arrow_down(draw, voice_cx, voice_boxes[i][3], voice_boxes[i + 1][1])

    s2y = gap_center_y((0, lane_y + 42, 0, chat_ys[0]), chat_boxes[0])
    draw_step_badge(draw, (chat_cx, s2y), "2", step_font)
    draw_step_badge(draw, (voice_cx, s2y), "2", step_font)

    # Data layer
    data_w = W - MARGIN * 2
    draw_lane_title(draw, MARGIN, data_title_y, data_w, "Datos compartidos (chat y voz)", COLORS["data_bg"], COLORS["data_border"], COLORS["data_text"], lane_font)
    col_w = (data_w - 40) // 3
    d1 = draw_box(draw, MARGIN, data_boxes_y, col_w, "Redis", ["Sesión: caso, paso, intentos"], data_style, box_title, box_body)
    d2 = draw_box(draw, MARGIN + col_w + 20, data_boxes_y, col_w, "Postgres", ["Casos, historial, flujos, métricas"], data_style, box_title, box_body)
    d3 = draw_box(draw, MARGIN + (col_w + 20) * 2, data_boxes_y, col_w, "S3", ["Fotos y audios presintetizados"], data_style, box_title, box_body)

    merge_mid = (chat_boxes[2][3] + data_title_y) // 2
    arrow_merge_down(draw, chat_cx, voice_cx, chat_boxes[2][3], W // 2, data_title_y)
    arrow_down(draw, W // 2, data_title_y + 34, data_boxes_y)

    s5y = (data_title_y + 34 + data_boxes_y) // 2
    draw_step_badge(draw, (W // 2, s5y), "5", step_font)
    arrow_down(draw, W // 2, max(d1[3], d2[3], d3[3]), resp_y)

    # Response
    resp_w = 640
    resp_x = (W - resp_w) // 2
    resp = draw_box(
        draw, resp_x, resp_y, resp_w,
        "Respuesta al operador",
        ["Chat: mensaje WhatsApp · Voz: guía hablada paso a paso", "Si no se resuelve: número de caso por WhatsApp"],
        chat_style, box_title, box_body,
    )
    s6y = gap_center_y(d2, resp)
    draw_step_badge(draw, (W // 2, s6y), "6", step_font)

    # Escalation
    esc_w = W - MARGIN * 2
    draw_lane_title(draw, MARGIN, esc_title_y, esc_w, "Escalamiento a mesa de ayuda (sin transferencia en vivo)", COLORS["mesa_bg"], COLORS["mesa_border"], COLORS["mesa_text"], lane_font)
    ew = (esc_w - 60) // 4
    gap_x = 20
    e1 = draw_box(draw, MARGIN, esc_boxes_y, ew, "Caso en Postgres", ["Prioridad y detalle del fallo"], mesa_style, box_title, box_body)
    e2 = draw_box(draw, MARGIN + ew + gap_x, esc_boxes_y, ew, "SES + consola", ["Correo y bandeja CloudFront + Cognito"], mesa_style, box_title, box_body)
    e3 = draw_box(draw, MARGIN + (ew + gap_x) * 2, esc_boxes_y, ew, "Mesa toma el caso", ["Evita doble llamada al operador"], mesa_style, box_title, box_body)
    e4 = draw_box(draw, MARGIN + (ew + gap_x) * 3, esc_boxes_y, ew, "Devuelve la llamada", ["Desde celular de la mesa por WhatsApp"], mesa_style, box_title, box_body)

    s7y = (resp[3] + esc_boxes_y) // 2
    draw_step_badge(draw, (W // 2, s7y), "7", step_font)
    arrow_down(draw, W // 2, resp[3], esc_boxes_y)

    flow_y = esc_boxes_y + (e1[3] - esc_boxes_y) // 2
    for a, b, num in [(e1, e2, "8"), (e2, e3, "9"), (e3, e4, "10")]:
        cx = (a[2] + b[0]) // 2
        draw_step_badge(draw, (cx, flow_y), num, step_font)
        arrow_right(draw, a[2], flow_y, b[0])

    return_y = e4[3] + 48
    arrow_left_dashed(draw, e4[0] + ew // 2, return_y, op_x + op_w, "llamada de vuelta", label_font)

    return img


def draw_table(width: int = W) -> Image.Image:
    table_head = font(16, bold=True)
    table_body = font(13)
    table_small = font(12)

    cols = [200, 430, 390]
    row_h = 54
    header_h = 42
    pad = 10
    rows = len(PIEZAS)
    height = header_h + rows * row_h + 60

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    draw.text((MARGIN, 16), "Piezas", fill=COLORS["title"], font=table_head)

    x0 = MARGIN
    y0 = 48
    table_w = sum(cols) + pad * 2
    rounded_rect(draw, (x0, y0, x0 + table_w, y0 + header_h + rows * row_h), 10, WHITE, COLORS["table_border"])

    headers = ["Pieza", "Qué hace", "Por qué así"]
    cx = x0 + pad
    for i, (header, cw) in enumerate(zip(headers, cols)):
        rounded_rect(draw, (cx, y0, cx + cw, y0 + header_h), 0, COLORS["table_header"], COLORS["table_header"])
        draw.text((cx + 8, y0 + 12), header, fill=WHITE, font=table_head)
        cx += cw

    for r, (piece, what, why) in enumerate(PIEZAS):
        ry = y0 + header_h + r * row_h
        fill = COLORS["table_row_a"] if r % 2 == 0 else COLORS["table_row_b"]
        draw.rectangle((x0 + 1, ry, x0 + table_w - 1, ry + row_h), fill=fill)
        draw.line((x0, ry + row_h, x0 + table_w, ry + row_h), fill=COLORS["table_border"], width=1)

        cx = x0 + pad
        values = [piece, what, why]
        fonts_use = [table_body, table_small, table_small]
        for cw, text, fnt in zip(cols, values, fonts_use):
            lines = wrap_text(text, fnt, cw - 16)
            ty = ry + 8
            for line in lines[:3]:
                draw.text((cx + 8, ty), line, fill=COLORS["title"], font=fnt)
                ty += 16
            cx += cw

    return img


def compose() -> None:
    diagram = draw_diagram()
    table = draw_table(W)

    gap = 24
    total_h = diagram.height + gap + table.height
    out = Image.new("RGB", (W, total_h), BG)
    out.paste(diagram, (0, 0))
    out.paste(table, (0, diagram.height + gap))

    diagram.save(OUT_DIAGRAM, "PNG", optimize=True)
    out.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({out.size[0]}x{out.size[1]})")
    print(f"Wrote {OUT_DIAGRAM} ({diagram.size[0]}x{diagram.size[1]})")


if __name__ == "__main__":
    compose()
