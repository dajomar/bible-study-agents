import os
import sys
import json
from pathlib import Path
from datetime import date, timedelta
from dotenv import load_dotenv
from supabase import create_client

# ============================================================
# CONFIGURACIÓN
# ============================================================

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

JSON_PATH = Path(__file__).parent / "plan_lectura.json"

USUARIO_EMAIL  = "davidmaza@gmail.com"
USUARIO_NOMBRE = "David"
FECHA_INICIO   = date(2026, 6, 3)   # Primer día del plan
DIA_DESCANSO   = 6                   # 0=lunes … 6=domingo

# Mapeo de abreviaturas del plan (español) → abreviaturas en BD (es_rvr.json)
PLAN_A_DB = {
    "1cr":  "1ch",  "2cr":  "2ch",  "1jn":  "1jo",  "2jn":  "2jo",  "3jn":  "3jo",
    "1re":  "1kgs", "2re":  "2kgs", "1sam": "1sm",  "2sam": "2sm",
    "1ti":  "1tm",  "2ti":  "2tm",
    "abd":  "ob",   "ap":   "re",   "cnt":  "so",   "col":  "cl",
    "ef":   "eph",  "esd":  "ezr",  "est":  "et",
    "flm":  "phm",  "flp":  "ph",   "ga":   "gl",
    "hab":  "hk",   "hag":  "hg",   "hch":  "act",  "heb":  "hb",
    "jer":  "jr",   "jon":  "jn",   "jos":  "js",
    "jue":  "jud",  "jud":  "jd",   # jue=Jueces, jud=Judas
    "jn":   "jo",                    # jn en plan = Juan (John)
    "lc":   "lk",   "mal":  "ml",   "mr":   "mk",
    "nah":  "na",   "neh":  "ne",   "os":   "ho",
    "pr":   "prv",  "ro":   "rm",   "sal":  "ps",
    "sof":  "zp",   "stg":  "jm",   "tit":  "tt",   "zac":  "zc",
}

# ============================================================
# HELPERS
# ============================================================

def siguiente_fecha(fecha_actual):
    """Avanza un día saltando el día de descanso."""
    siguiente = fecha_actual + timedelta(days=1)
    while siguiente.weekday() == DIA_DESCANSO:
        siguiente += timedelta(days=1)
    return siguiente


def paginar(supabase, tabla, select, filtros=None, orden=None):
    """Descarga todos los registros paginando de 1000 en 1000."""
    registros = []
    offset = 0
    page   = 1000
    while True:
        q = supabase.table(tabla).select(select)
        if filtros:
            for campo, valor in filtros.items():
                q = q.eq(campo, valor)
        if orden:
            q = q.order(orden)
        resultado = q.range(offset, offset + page - 1).execute()
        lote = resultado.data
        registros.extend(lote)
        if len(lote) < page:
            break
        offset += page
    return registros


# ============================================================
# CARGA PRINCIPAL
# ============================================================

def cargar_plan():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Verificar si ya hay sesiones
    existentes = supabase.table("bible_sesiones").select("id", count="exact").execute()
    if existentes.count and existentes.count > 0:
        print(f"Ya existen {existentes.count} sesiones. Abortando.")
        sys.exit(0)

    # --------------------------------------------------------
    # PASO 1 — Leer plan JSON
    # --------------------------------------------------------
    print(f"Leyendo {JSON_PATH.name}...")
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    plan_meta = data["plan"]
    sesiones  = data["sesiones"]
    print(f"  → {len(sesiones)} sesiones encontradas\n")

    # --------------------------------------------------------
    # PASO 2 — Precargar libros y capítulos desde Supabase
    # --------------------------------------------------------
    print("[1] Precargando libros y capítulos...")

    libros_db = supabase.table("bible_libros").select("id, abreviatura").execute().data
    id_por_abbrev_db = {l["abreviatura"]: l["id"] for l in libros_db}
    # Agregar entradas con abreviaturas del plan para lookup directo
    id_por_abbrev = {**id_por_abbrev_db}
    for abbrev_plan, abbrev_db in PLAN_A_DB.items():
        if abbrev_db in id_por_abbrev_db:
            id_por_abbrev[abbrev_plan] = id_por_abbrev_db[abbrev_db]

    caps_db = paginar(supabase, "bible_capitulos", "id, id_libro, numero")
    cap_id_map = {(c["id_libro"], c["numero"]): c["id"] for c in caps_db}

    print(f"  → {len(libros_db)} libros, {len(caps_db)} capítulos cargados")

    # --------------------------------------------------------
    # PASO 3 — Precargar primer y último versículo por capítulo
    # --------------------------------------------------------
    print("\n[2] Precargando versículos (primer y último por capítulo)...")

    # Recopilar cap_ids únicos que el plan necesita
    cap_ids_necesarios = set()
    for s in sesiones:
        id_libro = id_por_abbrev[s["abreviatura"]]
        cap_ids_necesarios.add(cap_id_map[(id_libro, s["capitulo_inicio"])])
        cap_ids_necesarios.add(cap_id_map[(id_libro, s["capitulo_fin"])])

    # Descargar todos los versículos de esos capítulos (solo id, id_capitulo, numero)
    todos_vers = paginar(supabase, "bible_versiculos", "id, id_capitulo, numero")

    primer_verso = {}  # cap_id → verse_id con numero=1
    ultimo_verso = {}  # cap_id → verse_id con mayor numero

    for v in todos_vers:
        cid = v["id_capitulo"]
        if cid not in cap_ids_necesarios:
            continue
        num = v["numero"]
        if num == 1:
            primer_verso[cid] = v["id"]
        if cid not in ultimo_verso or num > ultimo_verso.get(f"_n_{cid}", 0):
            ultimo_verso[f"_n_{cid}"] = num
            ultimo_verso[cid] = v["id"]

    print(f"  → {len(primer_verso)} primeros versículos, {len(ultimo_verso)//2} últimos versículos listos")

    # --------------------------------------------------------
    # PASO 4 — Crear usuario
    # --------------------------------------------------------
    print("\n[3] Creando usuario...")

    usuario_existente = (
        supabase.table("bible_usuarios")
        .select("id")
        .eq("email", USUARIO_EMAIL)
        .execute()
        .data
    )

    if usuario_existente:
        id_usuario = usuario_existente[0]["id"]
        print(f"  → Usuario ya existe: {id_usuario}")
    else:
        nuevo_usuario = (
            supabase.table("bible_usuarios")
            .insert({"email": USUARIO_EMAIL, "nombre": USUARIO_NOMBRE})
            .execute()
            .data
        )
        id_usuario = nuevo_usuario[0]["id"]
        print(f"  → Usuario creado: {id_usuario}")

    # --------------------------------------------------------
    # PASO 5 — Crear plan
    # --------------------------------------------------------
    print("\n[4] Creando plan...")

    nuevo_plan = (
        supabase.table("bible_planes")
        .insert({
            "id_usuario":  id_usuario,
            "nombre":      plan_meta["nombre"],
            "descripcion": plan_meta["descripcion"],
            "activo":      True,
        })
        .execute()
        .data
    )
    id_plan = nuevo_plan[0]["id"]
    print(f"  → Plan creado (id={id_plan}): {plan_meta['nombre']}")

    # --------------------------------------------------------
    # PASO 6 — Insertar sesiones
    # --------------------------------------------------------
    print(f"\n[5] Insertando {len(sesiones)} sesiones...")

    fecha_actual = FECHA_INICIO
    # Si el día de inicio ya es domingo, avanzar
    while fecha_actual.weekday() == DIA_DESCANSO:
        fecha_actual += timedelta(days=1)

    sesiones_data = []
    for s in sesiones:
        id_libro  = id_por_abbrev[s["abreviatura"]]
        cap_ini   = cap_id_map[(id_libro, s["capitulo_inicio"])]
        cap_fin   = cap_id_map[(id_libro, s["capitulo_fin"])]

        sesiones_data.append({
            "id_plan":            id_plan,
            "orden":              s["orden"],
            "versiculo_inicio_id": primer_verso[cap_ini],
            "versiculo_fin_id":   ultimo_verso[cap_fin],
            "fecha_programada":   fecha_actual.isoformat(),
            "completada":         False,
        })

        fecha_actual = siguiente_fecha(fecha_actual)

    # Insertar en lotes de 200
    BATCH = 200
    for i in range(0, len(sesiones_data), BATCH):
        lote = sesiones_data[i:i + BATCH]
        supabase.table("bible_sesiones").insert(lote).execute()
        print(f"  ✓ Sesiones {i+1}–{min(i+BATCH, len(sesiones_data))} insertadas")

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------
    fecha_fin = sesiones_data[-1]["fecha_programada"]
    print(f"\n{'='*50}")
    print(f"Plan cargado exitosamente")
    print(f"  Usuario:    {USUARIO_NOMBRE} ({USUARIO_EMAIL})")
    print(f"  Sesiones:   {len(sesiones_data)}")
    print(f"  Inicio:     {FECHA_INICIO.isoformat()}")
    print(f"  Fin aprox.: {fecha_fin}")
    print(f"  Descanso:   domingos")
    print(f"{'='*50}")


if __name__ == "__main__":
    cargar_plan()
