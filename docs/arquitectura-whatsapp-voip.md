# WhatsApp y agente de voz

Qué hay que construir y qué hay que dejar desplegado para acompañar al operador en el puesto. Los dos canales hablan con el mismo flujo. WhatsApp no es un bot y la llamada otro bot.

## Decisión de arranque

Un servicio propio (orquestador) con dos adaptadores:

- WhatsApp Cloud API, directo o por un BSP.
- Voz por WebSocket de audio (Media Streams o SIP) hacia ese mismo orquestador.

El procedimiento vive en archivos de flujo, no en el prompt. El modelo solo clasifica la intención, saca datos (cédula, puesto, serial) y traduce una frase libre a sí, no, no entendí o quiero un humano.

## Cómo se siente para el operador

WhatsApp abre con tres opciones: logueo, internet, tableta. Cada paso pide una sola acción y un botón o una respuesta de sí o no. Si manda una foto del ícono de carga, entra en una segunda iteración; el primer corte es texto.

La llamada hace lo mismo en voz, con una frase corta por turno. En un puesto hay ruido, así que cada confirmación acepta voz y teclado: 1 sí, 2 no, 0 hablar con una persona. La cédula se marca por teclado. Al inicio de la llamada se informa que la conversación puede quedar registrada, por la Ley 1581.

Reglas de escalamiento, iguales en los dos canales:

- Huella que no reconoce: caso prioritario a Dirección de Censo.
- Dos intentos fallidos de credenciales: escala.
- Un paso de conectividad o de carga que no cierra tras repetirlo: siguiente paso del árbol y, si el árbol se agota, soporte técnico o logística.
- El operador pide una persona en cualquier momento.

## Qué implementar

| Módulo | Responsabilidad | Primera versión |
| --- | --- | --- |
| Flujos | Árbol de primer logueo, sin internet y tableta dañada. Texto de cada paso, transición y tope de intentos. | YAML en el repo, editable por procesos. |
| Motor | Estado de la sesión, avance, intentos, motivo de escalamiento. | Python. Sin LLM en el camino feliz. |
| Clasificador | Intención inicial y lectura de la respuesta libre. | Una llamada corta al LLM, con salida cerrada. |
| Adaptador WhatsApp | Webhook, envío, botones, descarga de media. | Texto y botones. Foto y nota de voz después. |
| Adaptador de voz | Audio en tiempo real, corte de frase, interrupción, DTMF, transferencia. | Mismos tres flujos. |
| Sesión | Teléfono, caso abierto, paso actual. | Redis. |
| Casos | Transcripción enmascarada, resultado, puesto, tiempos. | Postgres. |
| Herramientas | Crear ticket, pedir reenvío, registrar novedad de equipo, escalar. | Ticket y novedad reales. Reenvío e inventario quedan como solicitud registrada hasta que exista API. |
| Handoff | Pasar historial a una persona. | En WhatsApp, bandeja. En voz, transferencia de la llamada y el id del caso. |

Identidad mínima antes de actuar sobre credenciales o equipo: cédula y un dato de verificación (puesto o correo enmascarado). No se pide ni se guarda la huella.

## Qué desplegar

Un solo ambiente de piloto, con esto encendido:

| Pieza | Dónde | Para qué |
| --- | --- | --- |
| Contenedor `gateway` | AWS, detrás de un balanceador con HTTPS | Webhook de WhatsApp y socket de audio. |
| Redis | ElastiCache, tamaño chico | Sesión de la conversación. |
| Postgres | RDS, tamaño chico | Casos e indicadores básicos. |
| Bucket | S3, cifrado, retención acotada | Fotos y grabaciones. Sin biometría. |
| Secretos | SSM o Secrets Manager | Tokens de Meta, voz, STT, TTS y LLM. |
| LLM por API | El proveedor que ya usen, o Bedrock | Solo clasificación y extracción. |
| STT en español | Deepgram u otro streaming `es` | Transcripción de la llamada. |
| TTS en español | Polly neural (es-US o es-MX) | Locución corta. |
| Número de WhatsApp | Meta Business, en verificación desde el día uno | La aprobación del nombre comercial tarda días. |
| DID Colombia | Trunk SIP o CPaaS con número local | Que la llamada del puesto no sea internacional. |
| Aviso de grabación | En el saludo de la llamada | Base para conservar el audio. |

La guía offline de la tableta, el tablero completo y el modelo local de CSC no entran en este despliegue. El contenedor queda preparado para cambiar el clasificador a un modelo en la VPC si el cliente lo exige.

## Tres formas de contratar el canal

El cerebro es el mismo. Cambia quién lleva el número y el audio.

| Opción | Cuándo conviene | Qué queda afuera de nuestra VPC |
| --- | --- | --- |
| Infobip para WhatsApp y voz | Un solo contrato, número de Colombia y operación en la región. Es la opción más sana si el piloto sale a puestos reales pronto. | Texto, audio y media pasan por Infobip y por Meta. |
| Twilio: WhatsApp + Programmable Voice (Media Streams) | Laboratorio y primera integración más rápida, con SDK maduro. | Igual: el audio pasa por Twilio. Hay que confirmar que entreguen un DID de Colombia; si no, no sirve para el puesto. |
| LiveKit en la VPC + trunk SIP colombiano | Cuando el cliente pida que el audio y la transcripción no salgan, alineado con el modelo local de CSC. | Meta sigue viendo WhatsApp. El audio de la llamada puede quedarse en la VPC. STT y TTS locales sustituyen a Deepgram y Polly. Más operación. |

Camino recomendado: piloto con Infobip si necesitan el número local ya, o con Twilio si el primer mes es laboratorio y el DID de Colombia está confirmado. El servicio propio no se ata al proveedor: el adaptador es una interfaz. LiveKit queda como el paso siguiente si aparece la restricción de soberanía, no como el primer despliegue.

Retell, Vapi o un contact center completo (Amazon Connect, Twilio Flex) aceleran una demo y meten la conversación en un producto que no controla el árbol de pasos. No son el camino de este repo.

## Corte de la primera entrega

1. Flujos de los tres casos y un simulador por consola, sin teléfono.
2. WhatsApp de texto con botones, ticket al escalar y bandeja simple para la mesa.
3. Llamada con el mismo árbol, DTMF y transferencia a la mesa.
4. Medición mínima: resuelta por el asistente, escalada, tiempo a primera respuesta, tiempo a cierre.

Fuera de ese corte: foto del cargador, nota de voz de WhatsApp, reenvío automático de credenciales, inventario, tablero por municipio y la app offline.

## Orden de trabajo

La verificación del número de WhatsApp y la compra del DID arrancan en paralelo al código: son el camino crítico, no un cierre.

1. Dejar los tres flujos escritos y probados en el simulador.
2. Publicar el webhook y cerrar el caso de conectividad por WhatsApp de punta a punta.
3. Sumar logueo y tableta, con ticket.
4. Conectar el socket de voz al mismo motor y probar la llamada con DTMF en un puesto ruidoso.
5. Recién ahí medir contra la meta de 40–60 % en conectividad y carga.

## Criterio de hecho del piloto

Un operador con el celular resuelve “sin internet” y “no carga” sin hablar con la mesa, por chat o por llamada, y cuando no puede, la mesa recibe un caso con puesto, síntoma, pasos ya intentados y el tramo de conversación.
