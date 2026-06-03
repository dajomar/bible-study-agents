import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# ============================================================
# CONFIGURACIÓN
# ============================================================

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

JSON_PATH  = Path(__file__).parent / "es_rvr.json"
BATCH_SIZE = 500

# Nombres en español — el JSON trae los nombres en inglés
NOMBRES_ES = {
    "gn":   "Génesis",          "ex":   "Éxodo",            "lv":  "Levítico",
    "nm":   "Números",          "dt":   "Deuteronomio",      "js":  "Josué",
    "jud":  "Jueces",           "rt":   "Rut",               "1sm": "1 Samuel",
    "2sm":  "2 Samuel",         "1kgs": "1 Reyes",           "2kgs":"2 Reyes",
    "1ch":  "1 Crónicas",       "2ch":  "2 Crónicas",        "ezr": "Esdras",
    "ne":   "Nehemías",         "et":   "Ester",             "job": "Job",
    "ps":   "Salmos",           "prv":  "Proverbios",        "ec":  "Eclesiastés",
    "so":   "Cantares",         "is":   "Isaías",            "jr":  "Jeremías",
    "lm":   "Lamentaciones",    "ez":   "Ezequiel",          "dn":  "Daniel",
    "ho":   "Oseas",            "jl":   "Joel",              "am":  "Amós",
    "ob":   "Abdías",           "jn":   "Jonás",             "mi":  "Miqueas",
    "na":   "Nahúm",            "hk":   "Habacuc",           "zp":  "Sofonías",
    "hg":   "Hageo",            "zc":   "Zacarías",          "ml":  "Malaquías",
    "mt":   "Mateo",            "mk":   "Marcos",            "lk":  "Lucas",
    "jo":   "Juan",             "act":  "Hechos",            "rm":  "Romanos",
    "1co":  "1 Corintios",      "2co":  "2 Corintios",       "gl":  "Gálatas",
    "eph":  "Efesios",          "ph":   "Filipenses",        "cl":  "Colosenses",
    "1ts":  "1 Tesalonicenses", "2ts":  "2 Tesalonicenses",  "1tm": "1 Timoteo",
    "2tm":  "2 Timoteo",        "tt":   "Tito",              "phm": "Filemón",
    "hb":   "Hebreos",          "jm":   "Santiago",          "1pe": "1 Pedro",
    "2pe":  "2 Pedro",          "1jo":  "1 Juan",            "2jo": "2 Juan",
    "3jo":  "3 Juan",           "jd":   "Judas",             "re":  "Apocalipsis",
}

# ============================================================
# HELPERS
# ============================================================

def insertar_en_lotes(supabase, tabla, registros):
    for i in range(0, len(registros), BATCH_SIZE):
        lote = registros[i:i + BATCH_SIZE]
        supabase.table(tabla).insert(lote).execute()


# ============================================================
# CARGA PRINCIPAL
# ============================================================

def cargar_biblia():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Verificar si ya está cargado
    existentes = supabase.table("bible_libros").select("id", count="exact").execute()
    if existentes.count and existentes.count > 0:
        print(f"La Biblia ya está cargada ({existentes.count} libros). Abortando.")
        sys.exit(0)

    # Leer JSON
    print(f"Leyendo {JSON_PATH.name}...")
    with open(JSON_PATH, encoding="utf-8-sig") as f:
        data = json.load(f)
    print(f"  → {len(data)} libros encontrados\n")

    # --------------------------------------------------------
    # PASO 1 — bible_libros
    # --------------------------------------------------------
    print("[1] Insertando bible_libros...")

    libros_data = []
    for i, libro in enumerate(data):
        orden = i + 1
        abbrev = libro["abbrev"]
        libros_data.append({
            "orden":       orden,
            "nombre":      NOMBRES_ES.get(abbrev, libro["name"]),
            "abreviatura": abbrev,
            "testamento":  "Antiguo" if orden <= 39 else "Nuevo",
        })

    supabase.table("bible_libros").insert(libros_data).execute()

    # Recuperar IDs asignados por Supabase
    libros_db = supabase.table("bible_libros").select("id, orden").order("orden").execute().data
    id_por_orden = {l["orden"]: l["id"] for l in libros_db}

    print(f"  → {len(libros_db)} libros insertados")

    # --------------------------------------------------------
    # PASO 2 — bible_capitulos y bible_versiculos (por libro)
    # --------------------------------------------------------
    print("\n[2] Insertando capítulos y versículos...")

    total_caps = 0
    total_vers = 0

    for i, libro in enumerate(data):
        orden_libro = i + 1
        id_libro    = id_por_orden[orden_libro]
        nombre      = NOMBRES_ES.get(libro["abbrev"], libro["name"])

        # Insertar capítulos del libro
        caps_data = [
            {"id_libro": id_libro, "numero": num + 1}
            for num in range(len(libro["chapters"]))
        ]
        supabase.table("bible_capitulos").insert(caps_data).execute()

        # Recuperar IDs de capítulos recién insertados
        caps_db = (
            supabase.table("bible_capitulos")
            .select("id, numero")
            .eq("id_libro", id_libro)
            .order("numero")
            .execute()
            .data
        )

        # Construir versículos
        versiculos_data = []
        for cap in caps_db:
            versos = libro["chapters"][cap["numero"] - 1]
            for num_ver, texto in enumerate(versos):
                versiculos_data.append({
                    "id_capitulo": cap["id"],
                    "numero":      num_ver + 1,
                    "texto":       texto,
                })

        insertar_en_lotes(supabase, "bible_versiculos", versiculos_data)

        total_caps += len(caps_db)
        total_vers += len(versiculos_data)

        print(f"  ✓ {nombre:25} {len(caps_db):3} caps  {len(versiculos_data):5} vers")

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------
    print(f"\n{'='*45}")
    print(f"Carga completada exitosamente")
    print(f"  Libros:     {len(data)}")
    print(f"  Capítulos:  {total_caps}")
    print(f"  Versículos: {total_vers}")
    print(f"{'='*45}")


if __name__ == "__main__":
    cargar_biblia()
