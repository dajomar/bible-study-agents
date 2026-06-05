#!/usr/bin/env python3
"""
descargar_y_cargar_versiones.py
Descarga RVR1960, NVI y TLA desde mrk214.github.io,
las convierte al formato estándar del proyecto e inserta
en Supabase incluyendo bible_secciones.

Uso:
    python3 scripts/descargar_y_cargar_versiones.py

Versiones que procesa:
    - RVR1960 (reemplaza la existente)
    - NVI
    - TLA
"""

import os
import sys
import json
import requests
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
BATCH_SIZE   = 500

VERSIONES = [
    {
        "version":    "RVR1960",
        "url":        "https://mrk214.github.io/snapshots/es___spa___spa/RVR1960_vid_149.json",
        "truncar":    True,   # Reemplaza la RVR1960 existente
    },
    {
        "version":    "NVI",
        "url":        "https://mrk214.github.io/snapshots/es___spa___spa/NVI_vid_128.json",
        "truncar":    False,
    },
    {
        "version":    "TLA",
        "url":        "https://mrk214.github.io/snapshots/es___spa___spa/TLA_vid_176.json",
        "truncar":    False,
    },
]

# Mapeo USFM → (orden, abreviatura, testamento, nombre_es)
MAPEO_USFM = {
    "GEN": (1,  "gn",   "Antiguo", "Génesis"),
    "EXO": (2,  "ex",   "Antiguo", "Éxodo"),
    "LEV": (3,  "lv",   "Antiguo", "Levítico"),
    "NUM": (4,  "nm",   "Antiguo", "Números"),
    "DEU": (5,  "dt",   "Antiguo", "Deuteronomio"),
    "JOS": (6,  "jos",  "Antiguo", "Josué"),
    "JDG": (7,  "jue",  "Antiguo", "Jueces"),
    "RUT": (8,  "rt",   "Antiguo", "Rut"),
    "1SA": (9,  "1sam", "Antiguo", "1 Samuel"),
    "2SA": (10, "2sam", "Antiguo", "2 Samuel"),
    "1KI": (11, "1re",  "Antiguo", "1 Reyes"),
    "2KI": (12, "2re",  "Antiguo", "2 Reyes"),
    "1CH": (13, "1cr",  "Antiguo", "1 Crónicas"),
    "2CH": (14, "2cr",  "Antiguo", "2 Crónicas"),
    "EZR": (15, "esd",  "Antiguo", "Esdras"),
    "NEH": (16, "neh",  "Antiguo", "Nehemías"),
    "EST": (17, "est",  "Antiguo", "Ester"),
    "JOB": (18, "job",  "Antiguo", "Job"),
    "PSA": (19, "sal",  "Antiguo", "Salmos"),
    "PRO": (20, "pr",   "Antiguo", "Proverbios"),
    "ECC": (21, "ec",   "Antiguo", "Eclesiastés"),
    "SNG": (22, "cnt",  "Antiguo", "Cantares"),
    "ISA": (23, "is",   "Antiguo", "Isaías"),
    "JER": (24, "jer",  "Antiguo", "Jeremías"),
    "LAM": (25, "lm",   "Antiguo", "Lamentaciones"),
    "EZK": (26, "ez",   "Antiguo", "Ezequiel"),
    "DAN": (27, "dn",   "Antiguo", "Daniel"),
    "HOS": (28, "os",   "Antiguo", "Oseas"),
    "JOL": (29, "jl",   "Antiguo", "Joel"),
    "AMO": (30, "am",   "Antiguo", "Amós"),
    "OBA": (31, "abd",  "Antiguo", "Abdías"),
    "JON": (32, "jon",  "Antiguo", "Jonás"),
    "MIC": (33, "mi",   "Antiguo", "Miqueas"),
    "NAM": (34, "nah",  "Antiguo", "Nahúm"),
    "HAB": (35, "hab",  "Antiguo", "Habacuc"),
    "ZEP": (36, "sof",  "Antiguo", "Sofonías"),
    "HAG": (37, "hag",  "Antiguo", "Hageo"),
    "ZEC": (38, "zac",  "Antiguo", "Zacarías"),
    "MAL": (39, "mal",  "Antiguo", "Malaquías"),
    "MAT": (40, "mt",   "Nuevo",   "Mateo"),
    "MRK": (41, "mr",   "Nuevo",   "Marcos"),
    "LUK": (42, "lc",   "Nuevo",   "Lucas"),
    "JHN": (43, "jn",   "Nuevo",   "Juan"),
    "ACT": (44, "hch",  "Nuevo",   "Hechos"),
    "ROM": (45, "ro",   "Nuevo",   "Romanos"),
    "1CO": (46, "1co",  "Nuevo",   "1 Corintios"),
    "2CO": (47, "2co",  "Nuevo",   "2 Corintios"),
    "GAL": (48, "ga",   "Nuevo",   "Gálatas"),
    "EPH": (49, "ef",   "Nuevo",   "Efesios"),
    "PHP": (50, "flp",  "Nuevo",   "Filipenses"),
    "COL": (51, "col",  "Nuevo",   "Colosenses"),
    "1TH": (52, "1ts",  "Nuevo",   "1 Tesalonicenses"),
    "2TH": (53, "2ts",  "Nuevo",   "2 Tesalonicenses"),
    "1TI": (54, "1ti",  "Nuevo",   "1 Timoteo"),
    "2TI": (55, "2ti",  "Nuevo",   "2 Timoteo"),
    "TIT": (56, "tit",  "Nuevo",   "Tito"),
    "PHM": (57, "flm",  "Nuevo",   "Filemón"),
    "HEB": (58, "heb",  "Nuevo",   "Hebreos"),
    "JAS": (59, "stg",  "Nuevo",   "Santiago"),
    "1PE": (60, "1pe",  "Nuevo",   "1 Pedro"),
    "2PE": (61, "2pe",  "Nuevo",   "2 Pedro"),
    "1JN": (62, "1jn",  "Nuevo",   "1 Juan"),
    "2JN": (63, "2jn",  "Nuevo",   "2 Juan"),
    "3JN": (64, "3jn",  "Nuevo",   "3 Juan"),
    "JUD": (65, "jud",  "Nuevo",   "Judas"),
    "REV": (66, "ap",   "Nuevo",   "Apocalipsis"),
}

# ============================================================
# HELPERS
# ============================================================

def insertar_en_lotes(supabase, tabla, registros):
    for i in range(0, len(registros), BATCH_SIZE):
        lote = registros[i:i + BATCH_SIZE]
        supabase.table(tabla).insert(lote).execute()


def descargar_json(url: str) -> dict:
    print(f"  → Descargando desde {url}...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def convertir(data: dict, version: str) -> tuple:
    """
    Convierte el JSON de mrk214 al formato estándar.
    Retorna (libros, secciones_por_abrev)
    donde secciones_por_abrev = { "gn": [ {capitulo, versiculo_inicio, titulo} ] }
    """
    libros = []
    secciones_por_abrev = {}

    for libro_raw in data["books"]:
        usfm_libro = libro_raw["book_usfm"]
        if usfm_libro not in MAPEO_USFM:
            continue

        orden, abrev, testamento, nombre = MAPEO_USFM[usfm_libro]
        capitulos = []
        secciones = []
        titulo_pendiente = None

        for cap_raw in libro_raw["chapters"]:
            # Ignorar introducciones y capítulos no canónicos
            if not cap_raw.get("is_chapter", False):
                continue

            # Extraer número de capítulo del USFM (ej: "GEN.1" → 1)
            try:
                num_cap = int(cap_raw["chapter_usfm"].split(".")[-1])
            except (ValueError, IndexError):
                continue

            versiculos = []
            titulo_pendiente = None

            for item in cap_raw["items"]:
                tipo = item.get("type", "")

                # Detectar títulos de sección
                if tipo in ("heading1", "heading2", "heading3", "s", "s1", "s2"):
                    lineas = item.get("lines", [])
                    if lineas:
                        titulo_pendiente = " ".join(lineas).strip()

                # Detectar versículos
                elif tipo == "verse":
                    nums = item.get("verse_numbers", [])
                    lineas = item.get("lines", [])

                    if not nums or not lineas:
                        continue

                    num_ver = nums[0]
                    texto = " ".join(lineas).strip()

                    if not texto:
                        continue

                    # Ignorar versículos duplicados — el primero gana
                    nums_existentes = {v["numero"] for v in versiculos}
                    if num_ver in nums_existentes:
                        continue

                    # Si hay título pendiente, lo asignamos a este versículo
                    if titulo_pendiente:
                        secciones.append({
                            "capitulo":        num_cap,
                            "versiculo_inicio": num_ver,
                            "titulo":          titulo_pendiente,
                        })
                        titulo_pendiente = None

                    versiculos.append({
                        "numero": num_ver,
                        "texto":  texto,
                    })

            if versiculos:
                capitulos.append({
                    "numero":    num_cap,
                    "versiculos": versiculos,
                })

        libros.append({
            "orden":       orden,
            "nombre":      nombre,
            "abreviatura": abrev,
            "testamento":  testamento,
            "capitulos":   capitulos,
        })

        if secciones:
            secciones_por_abrev[abrev] = secciones

    libros.sort(key=lambda x: x["orden"])
    return libros, secciones_por_abrev


# ============================================================
# CARGA EN SUPABASE
# ============================================================

def truncar_version(supabase, version: str):
    print(f"  → Verificando que {version} esté limpia en Supabase...")
    existentes = (
        supabase.table("bible_libros")
        .select("id", count="exact")
        .eq("version", version)
        .execute()
    )
    if existentes.count and existentes.count > 0:
        print(f"  ✗ Aún existen {existentes.count} libros de {version} en Supabase.")
        print(f"    Elimínalos manualmente desde el SQL editor de Supabase:")
        print(f"    1) DELETE FROM bible_versiculos WHERE id_capitulo IN (SELECT c.id FROM bible_capitulos c JOIN bible_libros l ON c.id_libro = l.id WHERE l.version = '{version}');")
        print(f"    2) DELETE FROM bible_capitulos WHERE id_libro IN (SELECT id FROM bible_libros WHERE version = '{version}');")
        print(f"    3) DELETE FROM bible_libros WHERE version = '{version}';")
        import sys; sys.exit(1)
    print(f"  → {version} limpia. Procediendo con la carga.")


def cargar_version(supabase, version: str, libros: list, secciones_por_abrev: dict):
    # --------------------------------------------------------
    # PASO 1 — bible_libros
    # --------------------------------------------------------
    print(f"\n  [1] Insertando bible_libros...")
    libros_data = [{
        "orden":       l["orden"],
        "nombre":      l["nombre"],
        "abreviatura": l["abreviatura"],
        "testamento":  l["testamento"],
        "version":     version,
    } for l in libros]

    supabase.table("bible_libros").insert(libros_data).execute()

    libros_db = (
        supabase.table("bible_libros")
        .select("id, orden, abreviatura")
        .eq("version", version)
        .order("orden")
        .execute()
        .data
    )
    id_por_orden = {l["orden"]: l["id"] for l in libros_db}
    id_por_abrev = {l["abreviatura"]: l["id"] for l in libros_db}
    print(f"     → {len(libros_db)} libros insertados")

    # --------------------------------------------------------
    # PASO 2 — bible_capitulos y bible_versiculos
    # --------------------------------------------------------
    print(f"  [2] Insertando capítulos y versículos...")

    total_caps = 0
    total_vers = 0

    for libro in libros:
        id_libro = id_por_orden[libro["orden"]]

        caps_data = [
            {"id_libro": id_libro, "numero": c["numero"]}
            for c in libro["capitulos"]
        ]
        supabase.table("bible_capitulos").insert(caps_data).execute()

        caps_db = (
            supabase.table("bible_capitulos")
            .select("id, numero")
            .eq("id_libro", id_libro)
            .order("numero")
            .execute()
            .data
        )
        id_por_cap = {c["numero"]: c["id"] for c in caps_db}

        versiculos_data = []
        for cap in libro["capitulos"]:
            id_cap = id_por_cap[cap["numero"]]
            for ver in cap["versiculos"]:
                versiculos_data.append({
                    "id_capitulo": id_cap,
                    "numero":      ver["numero"],
                    "texto":       ver["texto"],
                })

        insertar_en_lotes(supabase, "bible_versiculos", versiculos_data)

        total_caps += len(caps_db)
        total_vers += len(versiculos_data)

        print(f"     ✓ {libro['nombre']:25} {len(caps_db):3} caps  {len(versiculos_data):5} vers")

    # --------------------------------------------------------
    # PASO 3 — bible_secciones
    # --------------------------------------------------------
    print(f"  [3] Insertando secciones...")

    total_secs = 0
    secciones_data = []

    for abrev, secciones in secciones_por_abrev.items():
        id_libro = id_por_abrev.get(abrev)
        if not id_libro:
            continue
        for sec in secciones:
            secciones_data.append({
                "id_libro":         id_libro,
                "capitulo":         sec["capitulo"],
                "versiculo_inicio": sec["versiculo_inicio"],
                "titulo":           sec["titulo"],
            })

    insertar_en_lotes(supabase, "bible_secciones", secciones_data)
    total_secs = len(secciones_data)
    print(f"     → {total_secs} secciones insertadas")

    return total_caps, total_vers, total_secs


# ============================================================
# MAIN
# ============================================================

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    for config in VERSIONES:
        version = config["version"]
        print(f"\n{'='*55}")
        print(f"📖 Procesando {version}")
        print(f"{'='*55}")

        # Verificar si ya existe (excepto si truncar=True)
        if not config["truncar"]:
            existentes = (
                supabase.table("bible_libros")
                .select("id", count="exact")
                .eq("version", version)
                .execute()
            )
            if existentes.count and existentes.count > 0:
                print(f"  ⚠️  {version} ya está cargada ({existentes.count} libros). Omitiendo.")
                continue

        # Truncar si es necesario
        if config["truncar"]:
            truncar_version(supabase, version)

        # Descargar y convertir
        data = descargar_json(config["url"])
        libros, secciones_por_abrev = convertir(data, version)
        print(f"  → {len(libros)} libros convertidos")
        print(f"  → {sum(len(s) for s in secciones_por_abrev.values())} secciones encontradas")

        # Cargar en Supabase
        total_caps, total_vers, total_secs = cargar_version(
            supabase, version, libros, secciones_por_abrev
        )

        print(f"\n  ✅ {version} completada")
        print(f"     Libros     : {len(libros)}")
        print(f"     Capítulos  : {total_caps}")
        print(f"     Versículos : {total_vers:,}")
        print(f"     Secciones  : {total_secs}")

    print(f"\n{'='*55}")
    print(f"✅ Todas las versiones procesadas")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()