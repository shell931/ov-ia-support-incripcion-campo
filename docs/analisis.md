# Análisis de la propuesta

Fuente: [incripcion-campo.pdf](fuente/incripcion-campo.pdf). El PDF trae el mismo planteamiento dos veces: las páginas 1–5 incluyen plan e indicadores; las páginas 6–8 repiten contexto, canales y casos, y cierran en la información pendiente.

## Problema

La inscripción en campo corre en tabletas, en el puesto. Hoy la incidencia se resuelve con una guía en papel o escalando a mesa de ayuda y a la Dirección de Censo. El operador pierde el puesto mientras espera.

La restricción que define el diseño: si no hay internet o la tableta no enciende, el operador no puede pedir ayuda desde la tableta. El canal tiene que ser el celular (WhatsApp o llamada).

## Casos levantados

| Caso | Qué se hace hoy | Qué puede hacer el asistente |
| --- | --- | --- |
| Primer logueo (usuario, contraseña, huella) | Revisar correo, cédula como usuario, dedos indicados. Si falla, Dirección de Censo. | Guía y escalamiento. El reenvío de credenciales y el caso de huella salen del puesto, no los resuelve la tableta sola. |
| Tableta sin internet | Datos móviles, modo avión, reinicio. | Flujo guiado paso a paso, con confirmación en cada paso. |
| Tableta dañada, no enciende o no está en el puesto | Cable, tipo C, otra toma, otro adaptador. | Diagnóstico guiado y, si no enciende o no hay equipo, novedad a logística. |

La meta que propone el documento para conectividad y carga: 40–60 % de incidencias resueltas sin una persona.

## Solución que describe el PDF

Un agente de nivel 1 que identifica la incidencia, guía con la base oficial, ejecuta acciones (ticket, reenvío de credenciales, reporte de tableta) y entrega a un humano cuando no cierra.

Canales previstos:

- WhatsApp Business, canal principal: texto, notas de voz y fotos.
- Línea con voicebot, marcada en el PDF como fase 2, para quien no tiene datos o le cuesta escribir.
- Ayuda offline dentro de la app de la tableta.
- Consola web para la mesa de ayuda, con el historial y el diagnóstico ya armados.

Piezas:

- Orquestador que clasifica (logueo, conectividad, tableta, otro) y conduce el flujo.
- Base de conocimiento versionada, editable por procesos.
- Árboles deterministas en los pasos críticos. El modelo interpreta la respuesta libre y avanza; no redacta el procedimiento.
- Integraciones: tickets (ClickUp o la mesa actual), operador por cédula, reenvío de credenciales, inventario por puesto, aviso a logística.
- Handoff por regla (huella no reconocida, tres pasos fallidos, tableta sin solución) o porque el operador lo pide.
- Tablero: tipo, puesto, municipio, hora, porcentaje resuelto por la IA, tiempos, tabletas reincidentes.

## Datos y modelo

Cédula y biometría caen en la Ley 1581 de 2012. El asistente no guarda huellas; guarda el estado del caso. Los logs enmascaran la cédula.

El modelo puede ser un LLM por API (salida más rápida) o el modelo local de la propuesta CSC si el cliente exige que los datos no salgan. La plataforma puede compartirse.

## Alcance que traía el PDF y el ajuste pedido

El MVP del PDF es WhatsApp, consola humana, los tres flujos, tickets y un tablero básico. Deja fuera el voicebot, el reenvío automático de credenciales y el inventario logístico completo. La guía offline depende del equipo de la app.

El arranque que se va a construir incluye desde el comienzo WhatsApp y el agente de voz. La guía offline, el reenvío por API de Censo y el inventario completo siguen fuera de esta primera entrega.

## Respondido por el cliente (5 oct 2026)

- El operador se comunica por WhatsApp (chat y llamada) desde un celular con datos.
- La mesa atiende los casos; hoy no transfiere llamadas.
- Se puede usar nube siempre que no viaje información sensible.

## Pendiente de negocio

- Volumen de operadores, puestos y picos de jornada.
- Herramienta donde la mesa ve sus casos y si tiene API.
- Si Dirección de Censo expone consulta de operador y reenvío de credenciales.
- Incidencias además de las tres ya levantadas.
