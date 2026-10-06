#!/usr/bin/env python3
"""Genera docs/diagramas/infraestructura.png (diagrama + Piezas + costos)."""

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

COSTOS_SUBTITLE = (
    "15 operadores · 22 días/mes · ≈660 incidencias · 50 % chat / 50 % voz · ≈2.000 min de voz · "
    "precios de lista oct-2026, sin impuestos ni desarrollo"
)

# (concepto, detalle, usd_mes, tipo: group | row | total)
COSTOS = [
    ("AWS (us-east-1)", "", "≈ 215", "group"),
    ("ECS Fargate", "2× voice-agent (1 vCPU, 2 GB), gateway y worker (0,25 vCPU, 0,5 GB)", "90", "row"),
    ("Application Load Balancer", "Tráfico bajo", "22", "row"),
    ("NAT Gateway", "Uno, más tráfico de salida", "35", "row"),
    ("RDS Postgres", "db.t4g.micro, 20 GB, una zona", "15", "row"),
    ("ElastiCache Redis", "cache.t4g.micro", "12", "row"),
    ("WAF", "ACL y reglas administradas", "11", "row"),
    ("IPv4 públicas", "ALB y NAT", "11", "row"),
    ("CloudWatch", "Logs, métricas, alarmas", "10", "row"),
    ("S3, CloudFront, Secrets, ECR, Route 53", "", "8", "row"),
    ("Cognito, SES", "Dentro de la capa gratuita", "0", "row"),
    ("Voz e IA", "", "≈ 82", "group"),
    ("LiveKit Cloud, plan Ship", "Incluye 5.000 min SIP; se usan ≈2.000", "50", "row"),
    ("Deepgram Nova-3 streaming", "2.000 min × 0,0077", "15", "row"),
    ("LLM chico", "≈9.000 clasificaciones de ≈1.000 tokens", "10", "row"),
    ("Cartesia, plan Pro", "Solo frases dinámicas; pasos presintetizados", "7", "row"),
    ("WhatsApp", "", "≈ 3", "group"),
    ("Llamadas de WhatsApp", "Iniciadas por el operador; sin costo empresa", "0", "row"),
    ("Mensajes de WhatsApp", "1.000 gratis/mes; luego 0,0008 en Colombia", "3", "row"),
    ("Total mensual", "≈ COP 1,0 millón a 3.340 COP/US$", "≈ 300", "total"),
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


V_GAP = 56
SECTION_GAP = 68
LANE_GAP = 54
BADGE_R = 15
BOX_RADIUS = 12
LANE_H = 36
STROKE = 2
HEAD_W = 6
HEAD_L = 10


def draw_step_badge_at(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    number: str,
    badge_font: ImageFont.FreeTypeFont,
) -> None:
    x, y = center
    r = BADGE_R
    draw.ellipse((x - r, y - r, x + r, y + r), fill=COLORS["step"], outline=COLORS["step"])
    bbox = draw.textbbox((0, 0), number, font=badge_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x - tw / 2 - bbox[0], y - th / 2 - bbox[1]), number, fill=COLORS["step_text"], font=badge_font)


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
    pad: int = 14,
    step: str | None = None,
    badge_font: ImageFont.FreeTypeFont | None = None,
) -> tuple[int, int, int, int]:
    """Dibuja una caja. El número de paso va dentro, a la izquierda."""
    text_x = x + pad + (BADGE_R * 2 + 12 if step else 0)
    text_w = (x + w - pad) - text_x

    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(wrap_text(line, body_font, text_w))

    title_h = title_font.getbbox("Ag")[3] + 7
    line_h = body_font.getbbox("Ag")[3] + 5
    content_h = title_h + len(wrapped) * line_h
    h = max(pad * 2 + content_h, BADGE_R * 2 + pad * 2)

    box = (x, y, x + w, y + h)
    rounded_rect(draw, box, BOX_RADIUS, style["bg"], style["border"])

    if step:
        draw_step_badge_at(draw, (x + pad + BADGE_R, y + h // 2), step, badge_font or title_font)

    ty = y + (h - content_h) // 2
    draw.text((text_x, ty), title, fill=style["text"], font=title_font)
    ty += title_h
    for line in wrapped:
        draw.text((text_x, ty), line, fill=style["text"], font=body_font)
        ty += line_h
    return box


def draw_lane_title(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    text: str,
    bg: str,
    border: str,
    text_color: str,
    lane_font: ImageFont.FreeTypeFont,
    step: str | None = None,
    badge_font: ImageFont.FreeTypeFont | None = None,
) -> tuple[int, int, int, int]:
    bar = (x, y, x + w, y + LANE_H)
    rounded_rect(draw, bar, LANE_H // 2, bg, border, 1)
    tw = text_width(text, lane_font)
    cy = y + LANE_H // 2
    badge_w = BADGE_R * 2 + 10 if step else 0
    tx = x + (w - tw + badge_w) // 2
    if step:
        draw_step_badge_at(draw, (tx - badge_w + BADGE_R, cy), step, badge_font or lane_font)
    draw.text((tx, cy - lane_font.getbbox("Ag")[3] // 2 - 1), text, fill=text_color, font=lane_font)
    return bar


def _head_down(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    draw.polygon([(x, y), (x - HEAD_W, y - HEAD_L), (x + HEAD_W, y - HEAD_L)], fill=color)


def _head_right(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    draw.polygon([(x, y), (x - HEAD_L, y - HEAD_W), (x - HEAD_L, y + HEAD_W)], fill=color)


def connect_down(draw: ImageDraw.ImageDraw, x: int, y_from: int, y_to: int) -> None:
    """Flecha vertical entre el borde inferior de una caja y el superior de la siguiente."""
    if y_to - y_from < HEAD_L + 4:
        return
    draw.line((x, y_from, x, y_to - HEAD_L + 1), fill=COLORS["arrow"], width=STROKE)
    _head_down(draw, x, y_to, COLORS["arrow"])


def connect_right(draw: ImageDraw.ImageDraw, y: int, x_from: int, x_to: int) -> None:
    if x_to - x_from < HEAD_L + 4:
        return
    draw.line((x_from, y, x_to - HEAD_L + 1, y), fill=COLORS["arrow"], width=STROKE)
    _head_right(draw, x_to, y, COLORS["arrow"])


def connect_split(
    draw: ImageDraw.ImageDraw,
    x_from: int,
    y_from: int,
    targets: list[int],
    y_to: int,
) -> None:
    """Un origen arriba que se reparte en varios destinos abajo, con codo horizontal."""
    y_bus = y_from + (y_to - y_from) // 2
    span = targets + [x_from]
    draw.line((x_from, y_from, x_from, y_bus), fill=COLORS["arrow"], width=STROKE)
    draw.line((min(span), y_bus, max(span), y_bus), fill=COLORS["arrow"], width=STROKE)
    for tx in targets:
        draw.line((tx, y_bus, tx, y_to - HEAD_L + 1), fill=COLORS["arrow"], width=STROKE)
        _head_down(draw, tx, y_to, COLORS["arrow"])


def connect_merge(
    draw: ImageDraw.ImageDraw,
    sources: list[int],
    y_from: int,
    x_to: int,
    y_to: int,
) -> None:
    """Varios orígenes arriba que confluyen en un destino abajo, con codo horizontal."""
    y_bus = y_from + (y_to - y_from) // 2
    for sx in sources:
        draw.line((sx, y_from, sx, y_bus), fill=COLORS["arrow"], width=STROKE)
    draw.line((min(sources + [x_to]), y_bus, max(sources + [x_to]), y_bus), fill=COLORS["arrow"], width=STROKE)
    draw.line((x_to, y_bus, x_to, y_to - HEAD_L + 1), fill=COLORS["arrow"], width=STROKE)
    _head_down(draw, x_to, y_to, COLORS["arrow"])


def connect_down_dashed(draw: ImageDraw.ImageDraw, x: int, y_from: int, y_to: int, color: str) -> None:
    dash, gap = 9, 7
    y = y_from
    limit = y_to - HEAD_L + 1
    while y < limit:
        draw.line((x, y, x, min(y + dash, limit)), fill=color, width=STROKE)
        y += dash + gap
    draw.polygon([(x, y_to), (x - HEAD_W, y_to - HEAD_L), (x + HEAD_W, y_to - HEAD_L)], fill=color)


def box_height(
    w: int,
    title: str,
    lines: list[str],
    title_font: ImageFont.FreeTypeFont,
    body_font: ImageFont.FreeTypeFont,
    pad: int = 14,
    step: bool = False,
) -> int:
    """Alto que tendrá draw_box con los mismos parámetros, para la pasada de layout."""
    text_w = w - pad * 2 - (BADGE_R * 2 + 12 if step else 0)
    count = sum(len(wrap_text(line, body_font, text_w)) for line in lines)
    title_h = title_font.getbbox("Ag")[3] + 7
    line_h = body_font.getbbox("Ag")[3] + 5
    return max(pad * 2 + title_h + count * line_h, BADGE_R * 2 + pad * 2)


def draw_pill(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    text: str,
    bg: str,
    border: str,
    text_color: str,
    pill_font: ImageFont.FreeTypeFont,
) -> tuple[int, int, int, int]:
    h = 40
    rounded_rect(draw, (x, y, x + w, y + h), h // 2, bg, border, 2)
    tw = text_width(text, pill_font)
    draw.text((x + (w - tw) // 2, y + h // 2 - pill_font.getbbox("Ag")[3] // 2 - 1), text, fill=text_color, font=pill_font)
    return (x, y, x + w, y + h)


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

    lane_gap_x = 24
    lane_w = (W - MARGIN * 2 - lane_gap_x) // 2
    chat_x = MARGIN
    voice_x = MARGIN + lane_w + lane_gap_x
    inner_pad = 22
    inner_w = lane_w - inner_pad * 2
    chat_bx, voice_bx = chat_x + inner_pad, voice_x + inner_pad
    chat_cx, voice_cx = chat_x + lane_w // 2, voice_x + lane_w // 2
    center = W // 2

    chat_defs = [
        ("2", "Meta WhatsApp Cloud API", ["Recibe el mensaje del operador"], chat_style),
        ("3", "WAF + ALB → gateway → SQS", ["Responde 200 al webhook y encola el mensaje"], aws_style),
        ("4", "worker + motor de flujos", ["Clasifica con el LLM, responde y crea el caso si aplica"], aws_style),
    ]
    voice_defs = [
        ("2", "Meta → LiveKit Cloud", ["Llamada SIP, salas y cancelación de ruido"], voice_style),
        ("3", "voice-agent (LiveKit Agents)", ["Una sesión por llamada activa"], aws_style),
        ("4", "Deepgram → LLM → Cartesia", ["Escucha, interpreta y habla con audio de pasos en S3"], ai_style),
    ]
    data_defs = [
        ("Redis", ["Sesión: caso, paso e intentos"]),
        ("Postgres", ["Casos, historial, flujos y métricas"]),
        ("S3", ["Fotos y audios presintetizados"]),
    ]
    esc_defs = [
        ("7", "Caso en Postgres", ["Prioridad y detalle del fallo"]),
        ("8", "SES + consola", ["Correo y bandeja CloudFront + Cognito"]),
        ("9", "Mesa toma el caso", ["Evita doble llamada al operador"]),
        ("10", "Devuelve la llamada", ["Desde el celular de la mesa por WhatsApp"]),
    ]

    # --- pasada de layout ---
    op_w = 600
    op_x = (W - op_w) // 2
    op_y = 104
    op_h = box_height(op_w, "Operador en puesto de inscripción", ["WhatsApp: mensajes de texto o llamada de voz"], box_title, box_body, step=True)

    lane_y = op_y + op_h + SECTION_GAP
    row_y = lane_y + LANE_H + LANE_GAP

    row_ys: list[int] = []
    for (_, c_title, c_lines, _), (_, v_title, v_lines, _) in zip(chat_defs, voice_defs):
        row_ys.append(row_y)
        row_h = max(
            box_height(inner_w, c_title, c_lines, box_title, box_body, step=True),
            box_height(inner_w, v_title, v_lines, box_title, box_body, step=True),
        )
        row_y += row_h + V_GAP
    lanes_bottom = row_y - V_GAP

    data_lane_y = lanes_bottom + SECTION_GAP
    data_row_y = data_lane_y + LANE_H + LANE_GAP
    data_w = W - MARGIN * 2
    data_gap = 24
    col_w = (data_w - data_gap * 2) // 3
    data_h = max(box_height(col_w, t, l, box_title, box_body) for t, l in data_defs)

    resp_w = 700
    resp_x = (W - resp_w) // 2
    resp_lines = [
        "Chat: mensaje de WhatsApp · Voz: guía hablada paso a paso",
        "Si no se resuelve, envía el número de caso por WhatsApp",
    ]
    resp_y = data_row_y + data_h + SECTION_GAP
    resp_h = box_height(resp_w, "Respuesta al operador", resp_lines, box_title, box_body, step=True)

    esc_lane_y = resp_y + resp_h + SECTION_GAP
    esc_row_y = esc_lane_y + LANE_H + LANE_GAP
    esc_gap = 30
    ew = (data_w - esc_gap * 3) // 4
    esc_h = max(box_height(ew, t, l, box_title, box_body, step=True) for _, t, l in esc_defs)

    pill_y = esc_row_y + esc_h + 54
    H = pill_y + 40 + MARGIN

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # --- encabezado ---
    draw.text((MARGIN, 24), "Infraestructura del piloto — flujo paso a paso", fill=COLORS["title"], font=title_font)
    draw.text(
        (MARGIN, 62),
        "WhatsApp único canal · chat y llamada · escalamiento sin transferencia en vivo",
        fill=COLORS["subtitle"],
        font=subtitle_font,
    )
    badge_w = 212
    rounded_rect(draw, (W - MARGIN - badge_w, 26, W - MARGIN, 58), 8, COLORS["aws_bg"], COLORS["aws_border"], 1)
    draw.text((W - MARGIN - badge_w + 14, 35), "AWS us-east-1 · VPC privada", fill=COLORS["aws_text"], font=label_font)

    # --- paso 1 ---
    op_box = draw_box(
        draw, op_x, op_y, op_w,
        "Operador en puesto de inscripción",
        ["WhatsApp: mensajes de texto o llamada de voz"],
        {"bg": WHITE, "border": "#94a3b8", "text": COLORS["title"]},
        box_title, box_body, step="1", badge_font=step_font,
    )

    # --- carriles chat y voz ---
    chat_bar = draw_lane_title(draw, chat_x, lane_y, lane_w, "Flujo chat (mensajes)", COLORS["chat_bg"], COLORS["chat_border"], COLORS["chat_text"], lane_font)
    draw_lane_title(draw, voice_x, lane_y, lane_w, "Flujo voz (llamada de WhatsApp)", COLORS["voice_bg"], COLORS["voice_border"], COLORS["voice_text"], lane_font)
    connect_split(draw, center, op_box[3], [chat_cx, voice_cx], lane_y)

    chat_boxes: list[tuple[int, int, int, int]] = []
    voice_boxes: list[tuple[int, int, int, int]] = []
    for i, ((c_step, c_title, c_lines, c_style), (v_step, v_title, v_lines, v_style)) in enumerate(zip(chat_defs, voice_defs)):
        chat_boxes.append(draw_box(draw, chat_bx, row_ys[i], inner_w, c_title, c_lines, c_style, box_title, box_body, step=c_step, badge_font=step_font))
        voice_boxes.append(draw_box(draw, voice_bx, row_ys[i], inner_w, v_title, v_lines, v_style, box_title, box_body, step=v_step, badge_font=step_font))

    connect_down(draw, chat_cx, chat_bar[3], chat_boxes[0][1])
    connect_down(draw, voice_cx, chat_bar[3], voice_boxes[0][1])
    for i in range(len(row_ys) - 1):
        connect_down(draw, chat_cx, chat_boxes[i][3], chat_boxes[i + 1][1])
        connect_down(draw, voice_cx, voice_boxes[i][3], voice_boxes[i + 1][1])

    # --- paso 5: datos compartidos ---
    data_bar = draw_lane_title(
        draw, MARGIN, data_lane_y, data_w, "Datos compartidos por chat y voz",
        COLORS["data_bg"], COLORS["data_border"], COLORS["data_text"], lane_font,
        step="5", badge_font=step_font,
    )
    connect_merge(draw, [chat_cx, voice_cx], max(chat_boxes[-1][3], voice_boxes[-1][3]), center, data_lane_y)

    data_boxes = []
    data_cxs = []
    for i, (t, l) in enumerate(data_defs):
        dx = MARGIN + (col_w + data_gap) * i
        data_boxes.append(draw_box(draw, dx, data_row_y, col_w, t, l, data_style, box_title, box_body))
        data_cxs.append(dx + col_w // 2)
    connect_split(draw, center, data_bar[3], data_cxs, data_row_y)

    # --- paso 6: respuesta ---
    resp = draw_box(
        draw, resp_x, resp_y, resp_w, "Respuesta al operador", resp_lines,
        chat_style, box_title, box_body, step="6", badge_font=step_font,
    )
    connect_merge(draw, data_cxs, data_row_y + data_h, center, resp_y)

    # --- pasos 7 a 10: escalamiento ---
    esc_bar = draw_lane_title(
        draw, MARGIN, esc_lane_y, data_w, "Escalamiento a la mesa de ayuda (sin transferencia en vivo)",
        COLORS["mesa_bg"], COLORS["mesa_border"], COLORS["mesa_text"], lane_font,
    )
    connect_down(draw, center, resp[3], esc_lane_y)

    esc_boxes = []
    for i, (step_num, t, l) in enumerate(esc_defs):
        ex = MARGIN + (ew + esc_gap) * i
        esc_boxes.append(
            draw_box(draw, ex, esc_row_y, ew, t, l, mesa_style, box_title, box_body, step=step_num, badge_font=step_font)
        )
    connect_split(draw, center, esc_bar[3], [esc_boxes[0][0] + ew // 2], esc_row_y)

    flow_y = esc_row_y + esc_h // 2
    for a, b in zip(esc_boxes, esc_boxes[1:]):
        connect_right(draw, flow_y, a[2], b[0])

    # --- cierre del ciclo ---
    pill_w = 360
    pill_x = min(esc_boxes[-1][0] + ew // 2 - pill_w // 2, W - MARGIN - pill_w)
    pill = draw_pill(
        draw, pill_x, pill_y, pill_w, "Inscripción retomada en el puesto",
        COLORS["mesa_bg"], COLORS["mesa_border"], COLORS["mesa_text"], lane_font,
    )
    connect_down_dashed(draw, pill_x + pill_w // 2, esc_boxes[-1][3], pill_y, COLORS["mesa_border"])

    return img


def draw_section_table(
    title: str,
    subtitle: str | None,
    headers: list[str],
    cols: list[int],
    rows: list[tuple],
    *,
    row_height: int = 54,
    value_cols: int = 3,
    align_last_right: bool = False,
) -> Image.Image:
    table_head = font(16, bold=True)
    table_body = font(13)
    table_small = font(12)
    table_bold = font(13, bold=True)
    subtitle_font = font(12)

    header_h = 42
    pad = 10
    title_y = 16
    subtitle_y = 42 if subtitle else 0
    table_top = 48 if not subtitle else 62
    table_h = header_h + len(rows) * row_height
    height = table_top + table_h + 24

    img = Image.new("RGB", (W, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((MARGIN, title_y), title, fill=COLORS["title"], font=table_head)

    if subtitle:
        for i, line in enumerate(wrap_text(subtitle, subtitle_font, W - MARGIN * 2)):
            draw.text((MARGIN, subtitle_y + i * 16), line, fill=COLORS["subtitle"], font=subtitle_font)

    x0 = MARGIN
    y0 = table_top
    table_w = sum(cols) + pad * 2
    rounded_rect(draw, (x0, y0, x0 + table_w, y0 + table_h), 10, WHITE, COLORS["table_border"])

    cx = x0 + pad
    for ci, (header, cw) in enumerate(zip(headers, cols)):
        rounded_rect(draw, (cx, y0, cx + cw, y0 + header_h), 0, COLORS["table_header"], COLORS["table_header"])
        if ci == len(cols) - 1 and align_last_right:
            hx = cx + cw - 10 - text_width(header, table_head)
        else:
            hx = cx + 8
        draw.text((hx, y0 + 12), header, fill=WHITE, font=table_head)
        cx += cw

    for r, row in enumerate(rows):
        ry = y0 + header_h + r * row_height
        kind = row[-1] if len(row) > value_cols else "row"
        values = list(row[:value_cols])

        if kind == "group":
            fill = "#e2e8f0"
            fnt = table_bold
        elif kind == "total":
            fill = "#dbeafe"
            fnt = table_bold
        else:
            fill = COLORS["table_row_a"] if r % 2 == 0 else COLORS["table_row_b"]
            fnt = table_body

        draw.rectangle((x0 + 1, ry, x0 + table_w - 1, ry + row_height), fill=fill)
        draw.line((x0, ry + row_height, x0 + table_w, ry + row_height), fill=COLORS["table_border"], width=1)

        cx = x0 + pad
        fonts_use = [fnt, table_small if kind == "row" else fnt, fnt]
        last_col = len(cols) - 1
        for ci, (cw, text, fnt_use) in enumerate(zip(cols, values, fonts_use)):
            lines = wrap_text(text, fnt_use, cw - 16)[:3]
            ty = ry + (row_height - len(lines) * 16) // 2
            for line in lines:
                if ci == last_col and align_last_right:
                    tx = cx + cw - 10 - text_width(line, fnt_use)
                else:
                    tx = cx + 8
                draw.text((tx, ty), line, fill=COLORS["title"], font=fnt_use)
                ty += 16
            cx += cw

    return img


def draw_piezas_table() -> Image.Image:
    return draw_section_table(
        "Piezas",
        None,
        ["Pieza", "Qué hace", "Por qué así"],
        [200, 430, 390],
        [(*row, "row") for row in PIEZAS],
    )


def draw_costos_table() -> Image.Image:
    return draw_section_table(
        "Costos mensuales estimados del piloto",
        COSTOS_SUBTITLE,
        ["Concepto", "Detalle", "US$ / mes"],
        [260, 520, 110],
        COSTOS,
        row_height=40,
        align_last_right=True,
    )


def compose() -> None:
    diagram = draw_diagram()
    piezas = draw_piezas_table()
    costos = draw_costos_table()

    gap = 32
    y = 0
    total_h = diagram.height + gap + piezas.height + gap + costos.height
    out = Image.new("RGB", (W, total_h), BG)
    out.paste(diagram, (0, y))
    y += diagram.height + gap
    out.paste(piezas, (0, y))
    y += piezas.height + gap
    out.paste(costos, (0, y))

    diagram.save(OUT_DIAGRAM, "PNG", optimize=True)
    out.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({out.size[0]}x{out.size[1]})")
    print(f"Wrote {OUT_DIAGRAM} ({diagram.size[0]}x{diagram.size[1]})")


if __name__ == "__main__":
    compose()
