import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
from supabase import create_client
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ============================================================
# CONFIGURACIÓN
# ============================================================

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

SUPABASE_URL   = os.getenv("SUPABASE_URL")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY")
SLACK_TOKEN    = os.getenv("SLACK_TOKEN")
CANAL_ESTUDIO  = os.getenv("SLACK_CANAL_ESTUDIO", "#bible-study")
CANAL_ERRORES  = os.getenv("SLACK_CANAL_ERRORES", "#errores")
OLLAMA_URL     = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434") + "/api/generate"
MODELO         = "llama3.1"

# ============================================================
# CLIENTES
# ============================================================

supabase = None
slack    = None

# ============================================================
# PASO 1 — Obtener sesión del día
# ============================================================

def obtener_sesion_hoy():
    hoy = date.today().isoformat()
    resultado = (
        supabase.table("bible_sesiones")
        .select("id, orden, versiculo_inicio_id, versiculo_fin_id, id_plan")
        .eq("fecha_programada", hoy)
        .eq("completada", False)
        .limit(1)
        .execute()
    )
    if not resultado.data:
        raise ValueError(f"No hay sesión programada para hoy ({hoy}) o ya fue completada.")
    return resultado.data[0]

# ============================================================
# PASO 2 — Extraer versículos del pasaje
# ============================================================

def obtener_versiculos(versiculo_inicio_id, versiculo_fin_id):
    """Extrae todos los versículos entre el inicio y fin de la sesión."""

    # Obtener info del versículo de inicio (capitulo y numero)
    v_inicio = (
        supabase.table("bible_versiculos")
        .select("id, id_capitulo, numero")
        .eq("id", versiculo_inicio_id)
        .single()
        .execute()
        .data
    )
    v_fin = (
        supabase.table("bible_versiculos")
        .select("id, id_capitulo, numero")
        .eq("id", versiculo_fin_id)
        .single()
        .execute()
        .data
    )

    # Obtener info de los capítulos (numero y id_libro)
    cap_inicio = (
        supabase.table("bible_capitulos")
        .select("id, numero, id_libro")
        .eq("id", v_inicio["id_capitulo"])
        .single()
        .execute()
        .data
    )
    cap_fin = (
        supabase.table("bible_capitulos")
        .select("id, numero, id_libro")
        .eq("id", v_fin["id_capitulo"])
        .single()
        .execute()
        .data
    )

    id_libro = cap_inicio["id_libro"]

    # Obtener todos los capítulos del libro en ese rango
    caps = (
        supabase.table("bible_capitulos")
        .select("id, numero")
        .eq("id_libro", id_libro)
        .gte("numero", cap_inicio["numero"])
        .lte("numero", cap_fin["numero"])
        .order("numero")
        .execute()
        .data
    )

    cap_ids = [c["id"] for c in caps]

    # Obtener todos los versículos de esos capítulos
    versiculos = (
        supabase.table("bible_versiculos")
        .select("id, id_capitulo, numero, texto")
        .in_("id_capitulo", cap_ids)
        .order("id_capitulo")
        .order("numero")
        .execute()
        .data
    )

    # Obtener nombre del libro
    libro = (
        supabase.table("bible_libros")
        .select("nombre")
        .eq("id", id_libro)
        .single()
        .execute()
        .data
    )

    return versiculos, caps, libro["nombre"], cap_inicio["numero"], cap_fin["numero"]


def construir_texto_pasaje(versiculos, caps):
    """Formatea los versículos como texto legible para Llama."""
    cap_map = {c["id"]: c["numero"] for c in caps}
    lineas = []
    cap_actual = None

    for v in versiculos:
        num_cap = cap_map[v["id_capitulo"]]
        if num_cap != cap_actual:
            lineas.append(f"\n[Capítulo {num_cap}]")
            cap_actual = num_cap
        lineas.append(f"{v['numero']}. {v['texto']}")

    return "\n".join(lineas).strip()

# ============================================================
# PASO 3 — Analizar con Llama
# ============================================================

def analizar_con_llama(texto_pasaje, libro, cap_inicio, cap_fin):
    referencia = f"{libro} {cap_inicio}" if cap_inicio == cap_fin else f"{libro} {cap_inicio}–{cap_fin}"

    prompt = f"""Eres un teólogo experto en hermenéutica bíblica y contexto histórico, especializado en la Biblia Reina Valera 1960. Analiza el siguiente pasaje bíblico y responde en español con un JSON estructurado.

PASAJE: {referencia}

{texto_pasaje}

Responde ÚNICAMENTE con este JSON (sin texto adicional):
{{
  "contexto_historico": "<contexto histórico, cultural y geográfico del pasaje — explica el período, los personajes clave y su importancia, entre 4 y 6 párrafos>",
  "resumen": "<narra con detalle lo que ocurre en el pasaje, evento por evento, entre 4 y 6 párrafos>",
  "temas_principales": "<5 a 7 temas teológicos y espirituales con una breve explicación de cada uno, separados por punto y coma>",
  "conexiones": "<4 conexiones con otros pasajes o libros de la Biblia, explicando brevemente la relación>",
  "preguntas_reflexion": "<5 preguntas numeradas profundas para reflexión personal o grupal>"
}}"""

    payload = {
        "model":   MODELO,
        "prompt":  prompt,
        "stream":  False,
        "options": {
            "num_ctx":     32768,  # Ventana de contexto — prompt + respuesta
            "num_predict": 8192,   # Tokens máximos para la respuesta
            "temperature": 0.3,    # Más determinista para JSON estructurado
        },
    }

    inicio = time.time()
    try:
        respuesta = requests.post(OLLAMA_URL, json=payload, timeout=1800)
        respuesta.raise_for_status()
    except requests.ConnectionError:
        raise RuntimeError(f"Ollama no está corriendo en {OLLAMA_URL.replace('/api/generate','')}")
    except requests.Timeout:
        raise RuntimeError("Ollama no respondió — timeout de 5 minutos")

    duracion = round(time.time() - inicio, 2)
    data     = respuesta.json()
    texto    = data.get("response", "").strip()
    tokens   = data.get("eval_count", 0)

    # Extraer JSON de la respuesta
    inicio_json = texto.find("{")
    fin_json    = texto.rfind("}") + 1
    if inicio_json < 0:
        raise ValueError(f"Llama no devolvió JSON. Respuesta: {texto[:200]}")
    if fin_json <= inicio_json:
        raise ValueError(f"Respuesta truncada — Llama se quedó sin tokens. Longitud: {len(texto)} chars. Fragmento final: ...{texto[-200:]}")

    texto_json = texto[inicio_json:fin_json]
    try:
        analisis = json.loads(texto_json)
    except json.JSONDecodeError:
        # Llama a veces incluye comillas o saltos de línea sin escapar dentro de los valores.
        # Intentar extraer campo por campo con regex como fallback.
        import re
        analisis = {}
        campos = ["contexto_historico", "resumen", "temas_principales", "conexiones", "preguntas_reflexion"]
        for campo in campos:
            patron = rf'"{campo}"\s*:\s*"(.*?)"(?:\s*[,}}])'
            match = re.search(patron, texto_json, re.DOTALL)
            analisis[campo] = match.group(1).replace('\\"', '"') if match else ""
        if not any(analisis.values()):
            raise ValueError(f"No se pudo extraer el análisis. Respuesta: {texto[:300]}")
    analisis["tokens_usados"]     = tokens
    analisis["duracion_segundos"] = duracion

    return analisis

# ============================================================
# PASO 4 — Guardar análisis en Supabase
# ============================================================

def guardar_analisis(id_sesion, analisis):
    resultado = (
        supabase.table("bible_analisis")
        .insert({
            "id_sesion":          id_sesion,
            "contexto_historico": analisis.get("contexto_historico", ""),
            "resumen":            analisis.get("resumen", ""),
            "temas_principales":  analisis.get("temas_principales", ""),
            "conexiones":         analisis.get("conexiones", ""),
            "preguntas_reflexion":analisis.get("preguntas_reflexion", ""),
            "modelo_usado":       MODELO,
            "tokens_usados":      analisis.get("tokens_usados", 0),
            "duracion_segundos":  analisis.get("duracion_segundos", 0),
        })
        .execute()
    )
    return resultado.data[0]["id"]

# ============================================================
# PASO 5 — Marcar sesión como completada
# ============================================================

def marcar_completada(id_sesion):
    from datetime import datetime, timezone
    supabase.table("bible_sesiones").update({
        "completada":       True,
        "fecha_completada": datetime.now(timezone.utc).isoformat(),
    }).eq("id", id_sesion).execute()

# ============================================================
# PASO 6 — Notificar por Slack
# ============================================================

def notificar_estudio(sesion, analisis, libro, cap_inicio, cap_fin, id_analisis):
    referencia = f"{libro} {cap_inicio}" if cap_inicio == cap_fin else f"{libro} {cap_inicio}–{cap_fin}"

    mensaje = f"""📖 *Estudio bíblico del día — Sesión {sesion['orden']}*
*Pasaje:* {referencia}

*Resumen*
{analisis.get('resumen', '')}

*Contexto histórico*
{analisis.get('contexto_historico', '')}

*Temas principales*
{analisis.get('temas_principales', '')}

*Conexiones bíblicas*
{analisis.get('conexiones', '')}

*Preguntas de reflexión*
{analisis.get('preguntas_reflexion', '')}

_Modelo: {MODELO} · {analisis.get('duracion_segundos', 0)}s · análisis #{id_analisis}_"""

    try:
        slack.chat_postMessage(channel=CANAL_ESTUDIO, text=mensaje, mrkdwn=True)
    except SlackApiError as e:
        print(f"  ⚠ No se pudo enviar a Slack: {e}")


def notificar_error(mensaje):
    try:
        slack.chat_postMessage(
            channel=CANAL_ERRORES,
            text=f"🔴 *Bible Study — Error*\n{mensaje}",
            mrkdwn=True
        )
    except Exception:
        pass  # Si Slack falla, solo imprimir

# ============================================================
# AGENTE PRINCIPAL
# ============================================================

def correr_agente():
    global supabase, slack

    print("=" * 50)
    print("BIBLE STUDY — Agente 0 (Análisis diario)")
    print("=" * 50)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    slack    = WebClient(token=SLACK_TOKEN)

    try:
        # Paso 1 — Sesión del día
        print("\n[1] Buscando sesión de hoy...")
        sesion = obtener_sesion_hoy()
        print(f"  → Sesión {sesion['orden']} encontrada (id={sesion['id']})")

        # Paso 2 — Versículos
        print("\n[2] Extrayendo versículos...")
        versiculos, caps, libro, cap_inicio, cap_fin = obtener_versiculos(
            sesion["versiculo_inicio_id"],
            sesion["versiculo_fin_id"]
        )
        referencia = f"{libro} {cap_inicio}–{cap_fin}" if cap_inicio != cap_fin else f"{libro} {cap_inicio}"
        texto_pasaje = construir_texto_pasaje(versiculos, caps)
        print(f"  → {referencia} — {len(versiculos)} versículos")

        # Paso 3 — Llama
        print(f"\n[3] Enviando a Llama ({MODELO})...")
        analisis = analizar_con_llama(texto_pasaje, libro, cap_inicio, cap_fin)
        print(f"  → Análisis generado en {analisis['duracion_segundos']}s ({analisis['tokens_usados']} tokens)")

        # Paso 4 — Guardar
        print("\n[4] Guardando análisis en Supabase...")
        id_analisis = guardar_analisis(sesion["id"], analisis)
        print(f"  → Análisis guardado (id={id_analisis})")

        # Paso 5 — Marcar completada
        marcar_completada(sesion["id"])
        print(f"  → Sesión {sesion['orden']} marcada como completada")

        # Paso 6 — Slack
        print("\n[5] Enviando a Slack...")
        notificar_estudio(sesion, analisis, libro, cap_inicio, cap_fin, id_analisis)
        print(f"  → Enviado a {CANAL_ESTUDIO}")

        print(f"\n✓ Agente completado — {referencia}")

    except ValueError as e:
        print(f"\n⚠ {e}")
        notificar_error(str(e))
        sys.exit(0)  # Error de negocio — no es crítico

    except RuntimeError as e:
        print(f"\n✗ Error de infraestructura: {e}")
        notificar_error(str(e))
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        notificar_error(f"Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    correr_agente()
