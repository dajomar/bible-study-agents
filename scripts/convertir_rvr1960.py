#!/usr/bin/env python3
"""
convertir_rvr1960.py
Convierte el JSON de RVR1960 al formato estructurado para cargar en Supabase.

Entrada : RVR1960 - Spanish.json
Salida  : scripts/biblia_rvr1960_supabase.json

Estructura de salida:
[
  {
    "orden": 1,
    "nombre": "Génesis",
    "abreviatura": "gn",
    "testamento": "Antiguo",
    "capitulos": [
      {
        "numero": 1,
        "versiculos": [
          { "numero": 1, "texto": "En el principio creó Dios..." },
          ...
        ]
      }
    ]
  },
  ...
]
"""

import json
import os

# Ruta del archivo fuente — ajusta si está en otra carpeta
ARCHIVO_FUENTE = "RVR1960 - Spanish.json"
ARCHIVO_SALIDA = "scripts/biblia_rvr1960_supabase.json"

# Mapeo nombre en JSON → (abreviatura, testamento, orden canónico)
MAPEO_LIBROS = {
    "Génesis":           ("gn",   "Antiguo",  1),
    "Éxodo":             ("ex",   "Antiguo",  2),
    "Levítico":          ("lv",   "Antiguo",  3),
    "Números":           ("nm",   "Antiguo",  4),
    "Deuteronomio":      ("dt",   "Antiguo",  5),
    "Josué":             ("jos",  "Antiguo",  6),
    "Jueces":            ("jue",  "Antiguo",  7),
    "Rut":               ("rt",   "Antiguo",  8),
    "1 Samuel":          ("1sam", "Antiguo",  9),
    "2 Samuel":          ("2sam", "Antiguo", 10),
    "1 Reyes":           ("1re",  "Antiguo", 11),
    "2 Reyes":           ("2re",  "Antiguo", 12),
    "1 Crónicas":        ("1cr",  "Antiguo", 13),
    "2 Crónicas":        ("2cr",  "Antiguo", 14),
    "Esdras":            ("esd",  "Antiguo", 15),
    "Nehemías":          ("neh",  "Antiguo", 16),
    "Ester":             ("est",  "Antiguo", 17),
    "Job":               ("job",  "Antiguo", 18),
    "Salmos":            ("sal",  "Antiguo", 19),
    "Proverbios":        ("pr",   "Antiguo", 20),
    "Eclesiastés":       ("ec",   "Antiguo", 21),
    "Cantares":          ("cnt",  "Antiguo", 22),
    "Isaías":            ("is",   "Antiguo", 23),
    "Jeremías":          ("jer",  "Antiguo", 24),
    "Lamentaciones":     ("lm",   "Antiguo", 25),
    "Ezequiel":          ("ez",   "Antiguo", 26),
    "Daniel":            ("dn",   "Antiguo", 27),
    "Oseas":             ("os",   "Antiguo", 28),
    "Joel":              ("jl",   "Antiguo", 29),
    "Amós":              ("am",   "Antiguo", 30),
    "Abdías":            ("abd",  "Antiguo", 31),
    "Jonás":             ("jon",  "Antiguo", 32),
    "Miqueas":           ("mi",   "Antiguo", 33),
    "Nahúm":             ("nah",  "Antiguo", 34),
    "Habacuc":           ("hab",  "Antiguo", 35),
    "Sofonías":          ("sof",  "Antiguo", 36),
    "Hageo":             ("hag",  "Antiguo", 37),
    "Zacarías":          ("zac",  "Antiguo", 38),
    "Malaquías":         ("mal",  "Antiguo", 39),
    "S. Mateo":          ("mt",   "Nuevo",   40),
    "S. Marcos":         ("mr",   "Nuevo",   41),
    "S. Lucas":          ("lc",   "Nuevo",   42),
    "S.Juan":            ("jn",   "Nuevo",   43),
    "Hechos":            ("hch",  "Nuevo",   44),
    "Romanos":           ("ro",   "Nuevo",   45),
    "1 Corintios":       ("1co",  "Nuevo",   46),
    "2 Corintios":       ("2co",  "Nuevo",   47),
    "Gálatas":           ("ga",   "Nuevo",   48),
    "Efesios":           ("ef",   "Nuevo",   49),
    "Filipenses":        ("flp",  "Nuevo",   50),
    "Colosenses":        ("col",  "Nuevo",   51),
    "1 Tesalonicenses":  ("1ts",  "Nuevo",   52),
    "2 Tesalonicenses":  ("2ts",  "Nuevo",   53),
    "1 Timoteo":         ("1ti",  "Nuevo",   54),
    "2 Timoteo":         ("2ti",  "Nuevo",   55),
    "Tito":              ("tit",  "Nuevo",   56),
    "Filemón":           ("flm",  "Nuevo",   57),
    "Hebreos":           ("heb",  "Nuevo",   58),
    "Santiago":          ("stg",  "Nuevo",   59),
    "1 Pedro":           ("1pe",  "Nuevo",   60),
    "2 Pedro":           ("2pe",  "Nuevo",   61),
    "1 Juan":            ("1jn",  "Nuevo",   62),
    "2 Juan":            ("2jn",  "Nuevo",   63),
    "3 Juan":            ("3jn",  "Nuevo",   64),
    "Judas":             ("jud",  "Nuevo",   65),
    "Apocalipsis":       ("ap",   "Nuevo",   66),
}

# Nombres canónicos para mostrar (sin prefijo S.)
NOMBRES_CANONICOS = {
    "S. Mateo":  "Mateo",
    "S. Marcos": "Marcos",
    "S. Lucas":  "Lucas",
    "S.Juan":    "Juan",
}


def convertir():
    print("📖 Convirtiendo RVR1960 al formato Supabase...")
    print()

    # Cargar archivo fuente
    if not os.path.exists(ARCHIVO_FUENTE):
        print(f"✗ No se encontró el archivo: {ARCHIVO_FUENTE}")
        print(f"  Asegúrate de correr este script desde la carpeta donde está el JSON.")
        return

    with open(ARCHIVO_FUENTE, encoding="utf-8") as f:
        data = json.load(f)

    # Remover clave 'lang' si existe
    data.pop("lang", None)

    libros_convertidos = []
    errores = []
    total_versiculos = 0

    # Ordenar por orden canónico
    libros_ordenados = sorted(
        [(nombre, caps) for nombre, caps in data.items() if nombre in MAPEO_LIBROS],
        key=lambda x: MAPEO_LIBROS[x[0]][2]
    )

    libros_no_mapeados = [n for n in data.keys() if n not in MAPEO_LIBROS and n != "lang"]
    if libros_no_mapeados:
        print(f"⚠️  Libros no mapeados (se omiten): {libros_no_mapeados}")
        print()

    for nombre_json, capitulos_raw in libros_ordenados:
        abrev, testamento, orden = MAPEO_LIBROS[nombre_json]
        nombre_canonico = NOMBRES_CANONICOS.get(nombre_json, nombre_json)

        # Ordenar capítulos numéricamente
        capitulos_convertidos = []
        for num_cap_str in sorted(capitulos_raw.keys(), key=lambda x: int(x)):
            num_cap = int(num_cap_str)
            versiculos_raw = capitulos_raw[num_cap_str]

            # Ordenar versículos numéricamente
            versiculos_convertidos = []
            for num_ver_str in sorted(versiculos_raw.keys(), key=lambda x: int(x)):
                num_ver = int(num_ver_str)
                texto = versiculos_raw[num_ver_str].strip()

                if texto:
                    versiculos_convertidos.append({
                        "numero": num_ver,
                        "texto": texto
                    })
                    total_versiculos += 1

            capitulos_convertidos.append({
                "numero": num_cap,
                "versiculos": versiculos_convertidos
            })

        libros_convertidos.append({
            "orden": orden,
            "nombre": nombre_canonico,
            "abreviatura": abrev,
            "testamento": testamento,
            "capitulos": capitulos_convertidos
        })

        print(f"  ✅ [{orden:02d}] {nombre_canonico} — {len(capitulos_convertidos)} capítulos")

    # Guardar resultado
    os.makedirs("scripts", exist_ok=True)
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(libros_convertidos, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 50)
    print(f"✅ Conversión completada")
    print(f"   Libros convertidos : {len(libros_convertidos)}/66")
    print(f"   Total versículos   : {total_versiculos:,}")
    print(f"   Archivo generado   : {ARCHIVO_SALIDA}")


if __name__ == "__main__":
    convertir()