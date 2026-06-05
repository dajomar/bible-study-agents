#!/usr/bin/env python3
"""
cargar_biblia_rvr1960.py
Carga la Biblia completa RVR1960 desde el JSON nuevo a Supabase.

Formato de entrada esperado:
{
  "Génesis": {
    "1": {
      "1": "En el principio creó Dios...",
      "2": "Y la tierra estaba..."
    }
  }
}

Tablas que puebla:
  - bible_libros
  - bible_capitulos
  - bible_versiculos
"""

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

JSON_PATH  = Path(__file__).parent / "RVR1960 - Spanish.json"
BATCH_SIZE = 500

# Orden canónico + abreviatura + testamento por nombre del libro en el JSON
MAPEO_LIBROS = {
    "Génesis":          (1,  "gn",   "Antiguo"),
    "Éxodo":            (2,  "ex",   "Antiguo"),
    "Levítico":         (3,  "lv",   "Antiguo"),
    "Números":          (4,  "nm",   "Antiguo"),
    "Deuteronomio":     (5,  "dt",   "Antiguo"),
    "Josué":            (6,  "jos",  "Antiguo"),
    "Jueces":           (7,  "jue",  "Antiguo"),
    "Rut":              (8,  "rt",   "Antiguo"),
    "1 Samuel":         (9,  "1sam", "Antiguo"),
    "2 Samuel":         (10, "2sam", "Antiguo"),
    "1 Reyes":          (11, "1re",  "Antiguo"),
    "2 Reyes":          (12, "2re",  "Antiguo"),
    "1 Crónicas":       (13, "1cr",  "Antiguo"),
    "2 Crónicas":       (14, "2cr",  "Antiguo"),
    "Esdras":           (15, "esd",  "Antiguo"),
    "Nehemías":         (16, "neh",  "Antiguo"),
    "Ester":            (17, "est",  "Antiguo"),
    "Job":              (18, "job",  "Antiguo"),
    "Salmos":           (19, "sal",  "Antiguo"),
    "Proverbios":       (20, "pr",   "Antiguo"),
    "Eclesiastés":      (21, "ec",   "Antiguo"),
    "Cantares":         (22, "cnt",  "Antiguo"),
    "Isaías":           (23, "is",   "Antiguo"),
    "Jeremías":         (24, "jer",  "Antiguo"),
    "Lamentaciones":    (25, "lm",   "Antiguo"),
    "Ezequiel":         (26, "ez",   "Antiguo"),
    "Daniel":           (27, "dn",   "Antiguo"),
    "Oseas":            (28, "os",   "Antiguo"),
    "Joel":             (29, "jl",   "Antiguo"),
    "Amós":             (30, "am",   "Antiguo"),
    "Abdías":           (31, "abd",  "Antiguo"),
    "Jonás":            (32, "jon",  "Antiguo"),
    "Miqueas":          (33, "mi",   "Antiguo"),
    "Nahúm":            (34, "nah",  "Antiguo"),
    "Habacuc":          (35, "hab",  "Antiguo"),
    "Sofonías":         (36, "sof",  "Antiguo"),
    "Hageo":            (37, "hag",  "Antiguo"),
    "Zacarías":         (38, "zac",  "Antiguo"),
    "Malaquías":        (39, "mal",  "Antiguo"),
    "S. Mateo":         (40, "mt",   "Nuevo"),
    "S. Marcos":        (41, "mr",   "Nuevo"),
    "S. Lucas":         (42, "lc",   "Nuevo"),
    "S.Juan":           (43, "jn",   "Nuevo"),
    "Hechos":           (44, "hch",  "Nuevo"),
    "Romanos":          (45, "ro",   "Nuevo"),
    "1 Corintios":      (46, "1co",  "Nuevo"),
    "2 Corintios":      (47, "2co",  "Nuevo"),
    "Gálatas":          (48, "ga",   "Nuevo"),
    "Efesios":          (49, "ef",   "Nuevo"),
    "Filipenses":       (50, "flp",  "Nuevo"),
    "Colosenses":       (51, "col",  "Nuevo"),
    "1 Tesalonicenses": (52, "1ts",  "Nuevo"),
    "2 Tesalonicenses": (53, "2ts",  "Nuevo"),
    "1 Timoteo":        (54, "1ti",  "Nuevo"),
    "2 Timoteo":        (55, "2ti",  "Nuevo"),
    "Tito":             (56, "tit",  "Nuevo"),
    "Filemón":          (57, "flm",  "Nuevo"),
    "Hebreos":          (58, "heb",  "Nuevo"),
    "Santiago":         (59, "stg",  "Nuevo"),
    "1 Pedro":          (60, "1pe",  "Nuevo"),
    "2 Pedro":          (61, "2pe",  "Nuevo"),
    "1 Juan":           (62, "1jn",  "Nuevo"),
    "2 Juan":           (63, "2jn",  "Nuevo"),
    "3 Juan":           (64, "3jn",  "Nuevo"),
    "Judas":            (65, "jud",  "Nuevo"),
    "Apocalipsis":      (66, "ap",   "Nuevo"),
}

# Nombres canónicos sin prefijo S.
NOMBRES_CANONICOS = {
    "S. Mateo":  "Mateo",
    "S. Marcos": "Marcos",
    "S. Lucas":  "Lucas",
    "S.Juan":    "Juan",
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
        print("Si deseas recargar, trunca primero las tablas en Supabase.")
        sys.exit(0)

    # Leer JSON
    print(f"Leyendo {JSON_PATH.name}...")
    with open(JSON_PATH, encoding="utf-8-sig") as f:
        data = json.load(f)

    # Remover clave 'lang' si existe
    data.pop("lang", None)
    print(f"  → {len(data)} libros encontrados en el JSON\n")

    # Ordenar libros por orden canónico
    libros_ordenados = sorted(
        [(nombre, caps) for nombre, caps in data.items() if nombre in MAPEO_LIBROS],
        key=lambda x: MAPEO_LIBROS[x[0]][0]
    )

    libros_no_mapeados = [n for n in data.keys() if n not in MAPEO_LIBROS]
    if libros_no_mapeados:
        print(f"⚠️  Ignorando claves no reconocidas: {libros_no_mapeados}\n")

    # --------------------------------------------------------
    # PASO 1 — bible_libros
    # --------------------------------------------------------
    print("[1] Insertando bible_libros...")

    libros_data = []
    for nombre_json, _ in libros_ordenados:
        orden, abrev, testamento = MAPEO_LIBROS[nombre_json]
        nombre_canonico = NOMBRES_CANONICOS.get(nombre_json, nombre_json)
        libros_data.append({
            "orden":       orden,
            "nombre":      nombre_canonico,
            "abreviatura": abrev,
            "testamento":  testamento,
            "version":     "RVR1960",
        })

    supabase.table("bible_libros").insert(libros_data).execute()

    # Recuperar IDs asignados por Supabase
    libros_db = supabase.table("bible_libros").select("id, orden").order("orden").execute().data
    id_por_orden = {l["orden"]: l["id"] for l in libros_db}
    print(f"  → {len(libros_db)} libros insertados\n")

    # --------------------------------------------------------
    # PASO 2 — bible_capitulos y bible_versiculos
    # --------------------------------------------------------
    print("[2] Insertando capítulos y versículos...")

    total_caps = 0
    total_vers = 0

    for nombre_json, capitulos_raw in libros_ordenados:
        orden, abrev, testamento = MAPEO_LIBROS[nombre_json]
        nombre_canonico = NOMBRES_CANONICOS.get(nombre_json, nombre_json)
        id_libro = id_por_orden[orden]

        # Ordenar capítulos numéricamente
        nums_capitulos = sorted(capitulos_raw.keys(), key=lambda x: int(x))

        # Insertar capítulos
        caps_data = [
            {"id_libro": id_libro, "numero": int(num)}
            for num in nums_capitulos
        ]
        supabase.table("bible_capitulos").insert(caps_data).execute()

        # Recuperar IDs de capítulos
        caps_db = (
            supabase.table("bible_capitulos")
            .select("id, numero")
            .eq("id_libro", id_libro)
            .order("numero")
            .execute()
            .data
        )
        id_por_cap = {c["numero"]: c["id"] for c in caps_db}

        # Construir versículos
        versiculos_data = []
        for num_cap_str in nums_capitulos:
            num_cap = int(num_cap_str)
            id_capitulo = id_por_cap[num_cap]
            versiculos_raw = capitulos_raw[num_cap_str]

            # Ordenar versículos numéricamente
            for num_ver_str in sorted(versiculos_raw.keys(), key=lambda x: int(x)):
                texto = versiculos_raw[num_ver_str].strip()
                if texto:
                    versiculos_data.append({
                        "id_capitulo": id_capitulo,
                        "numero":      int(num_ver_str),
                        "texto":       texto,
                    })

        insertar_en_lotes(supabase, "bible_versiculos", versiculos_data)

        total_caps += len(caps_db)
        total_vers += len(versiculos_data)

        print(f"  ✓ {nombre_canonico:25} {len(caps_db):3} caps  {len(versiculos_data):5} vers")

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"✅ Carga completada exitosamente")
    print(f"   Libros     : {len(libros_ordenados)}")
    print(f"   Capítulos  : {total_caps}")
    print(f"   Versículos : {total_vers:,}")
    print(f"{'='*50}")


if __name__ == "__main__":
    cargar_biblia()