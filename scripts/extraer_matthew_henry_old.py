#!/usr/bin/env python3
"""
extraer_matthew_henry.py
Extrae los comentarios de Matthew Henry del PDF y los convierte
al formato estándar JSON para cargar en Supabase.

Entrada : comentario-de-la-biblia-matthew-henry.pdf
Salida  : scripts/comentarios_matthew_henry.json

Formato de salida:
[
  {
    "abreviatura_libro": "gn",
    "capitulo": 1,
    "titulo_capitulo": "Versículos 1—3. Dios crea...",
    "versiculo_inicio": 1,
    "versiculo_fin": 3,
    "titulo_seccion": "Dios crea los cielos y la tierra",
    "texto": "El primer versículo de la Biblia...",
    "autor": "matthew_henry"
  }
]

Uso:
    python3 scripts/extraer_matthew_henry.py <ruta_del_pdf>
    python3 scripts/extraer_matthew_henry.py "comentario-de-la-biblia-matthew-henry.pdf"
"""

import re
import sys
import json
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("Instalando pdfplumber...")
    import subprocess
    subprocess.run(["pip3", "install", "pdfplumber", "--break-system-packages", "-q"])
    import pdfplumber

# ============================================================
# MAPEO DE LIBROS — nombre en PDF → abreviatura estándar
# ============================================================

MAPEO_LIBROS = {
    "GÉNESIS": "gn", "GENESIS": "gn",
    "ÉXODO": "ex", "EXODO": "ex",
    "LEVÍTICO": "lv", "LEVITICO": "lv",
    "NÚMEROS": "nm", "NUMEROS": "nm",
    "DEUTERONOMIO": "dt",
    "JOSUÉ": "jos", "JOSUE": "jos",
    "JUECES": "jue",
    "RUT": "rt",
    "1 SAMUEL": "1sam",
    "2 SAMUEL": "2sam",
    "1 REYES": "1re",
    "2 REYES": "2re",
    "1 CRÓNICAS": "1cr", "1 CRONICAS": "1cr",
    "2 CRÓNICAS": "2cr", "2 CRONICAS": "2cr",
    "ESDRAS": "esd",
    "NEHEMÍAS": "neh", "NEHEMIAS": "neh",
    "ESTER": "est",
    "JOB": "job",
    "SALMOS": "sal",
    "PROVERBIOS": "pr",
    "ECLESIASTÉS": "ec", "ECLESIASTES": "ec",
    "CANTARES": "cnt",
    "ISAÍAS": "is", "ISAIAS": "is",
    "JEREMÍAS": "jer", "JEREMIAS": "jer",
    "LAMENTACIONES": "lm",
    "EZEQUIEL": "ez",
    "DANIEL": "dn",
    "OSEAS": "os",
    "JOEL": "jl",
    "AMÓS": "am", "AMOS": "am",
    "ABDÍAS": "abd", "ABDIAS": "abd",
    "JONÁS": "jon", "JONAS": "jon",
    "MIQUEAS": "mi",
    "NAHÚM": "nah", "NAHUM": "nah",
    "HABACUC": "hab",
    "SOFONÍAS": "sof", "SOFONIAS": "sof",
    "HAGEO": "hag",
    "ZACARÍAS": "zac", "ZACARIAS": "zac",
    "MALAQUÍAS": "mal", "MALAQUIAS": "mal",
    "MATEO": "mt",
    "MARCOS": "mr",
    "LUCAS": "lc",
    "JUAN": "jn",
    "HECHOS": "hch",
    "ROMANOS": "ro",
    "1 CORINTIOS": "1co",
    "2 CORINTIOS": "2co",
    "GÁLATAS": "ga", "GALATAS": "ga",
    "EFESIOS": "ef",
    "FILIPENSES": "flp",
    "COLOSENSES": "col",
    "1 TESALONICENSES": "1ts",
    "2 TESALONICENSES": "2ts",
    "1 TIMOTEO": "1ti",
    "2 TIMOTEO": "2ti",
    "TITO": "tit",
    "FILEMÓN": "flm", "FILEMON": "flm",
    "HEBREOS": "heb",
    "SANTIAGO": "stg",
    "1 PEDRO": "1pe",
    "2 PEDRO": "2pe",
    "1 JUAN": "1jn",
    "2 JUAN": "2jn",
    "3 JUAN": "3jn",
    "JUDAS": "jud",
    "APOCALIPSIS": "ap",
}

# Números romanos → arábigos
ROMANOS = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20,
    "XXI": 21, "XXII": 22, "XXIII": 23, "XXIV": 24, "XXV": 25,
    "XXVI": 26, "XXVII": 27, "XXVIII": 28, "XXIX": 29, "XXX": 30,
    "XXXI": 31, "XXXII": 32, "XXXIII": 33, "XXXIV": 34, "XXXV": 35,
    "XXXVI": 36, "XXXVII": 37, "XXXVIII": 38, "XXXIX": 39, "XL": 40,
    "XLI": 41, "XLII": 42, "XLIII": 43, "XLIV": 44, "XLV": 45,
    "XLVI": 46, "XLVII": 47, "XLVIII": 48, "XLIX": 49, "L": 50,
    "LI": 51, "LII": 52, "LIII": 53, "LIV": 54, "LV": 55,
    "LVI": 56, "LVII": 57, "LVIII": 58, "LIX": 59, "LX": 60,
    "LXI": 61, "LXII": 62, "LXIII": 63, "LXIV": 64, "LXV": 65,
    "LXVI": 66, "LXVII": 67, "LXVIII": 68, "LXIX": 69, "LXX": 70,
    "LXXI": 71, "LXXII": 72, "LXXIII": 73, "LXXIV": 74, "LXXV": 75,
    "LXXVI": 76, "LXXVII": 77, "LXXVIII": 78, "LXXIX": 79, "LXXX": 80,
    "LXXXI": 81, "LXXXII": 82, "LXXXIII": 83, "LXXXIV": 84, "LXXXV": 85,
    "LXXXVI": 86, "LXXXVII": 87, "LXXXVIII": 88, "LXXXIX": 89, "XC": 90,
    "XCI": 91, "XCII": 92, "XCIII": 93, "XCIV": 94, "XCV": 95,
    "XCVI": 96, "XCVII": 97, "XCVIII": 98, "XCIX": 99, "C": 100,
    "CI": 101, "CII": 102, "CIII": 103, "CIV": 104, "CV": 105,
    "CVI": 106, "CVII": 107, "CVIII": 108, "CIX": 109, "CX": 110,
    "CXI": 111, "CXII": 112, "CXIII": 113, "CXIV": 114, "CXV": 115,
    "CXVI": 116, "CXVII": 117, "CXVIII": 118, "CXIX": 119, "CXX": 120,
    "CXXI": 121, "CXXII": 122, "CXXIII": 123, "CXXIV": 124, "CXXV": 125,
    "CXXVI": 126, "CXXVII": 127, "CXXVIII": 128, "CXXIX": 129, "CXXX": 130,
    "CXXXI": 131, "CXXXII": 132, "CXXXIII": 133, "CXXXIV": 134, "CXXXV": 135,
    "CXXXVI": 136, "CXXXVII": 137, "CXXXVIII": 138, "CXXXIX": 139, "CXL": 140,
    "CXLI": 141, "CXLII": 142, "CXLIII": 143, "CXLIV": 144, "CXLV": 145,
    "CXLVI": 146, "CXLVII": 147, "CXLVIII": 148, "CXLIX": 149, "CL": 150,
}

def romano_a_arabigo(romano: str) -> int:
    return ROMANOS.get(romano.strip().upper(), 0)

def limpiar_texto(texto: str) -> str:
    """Limpia el texto extraído del PDF."""
    texto = texto.replace("\f", " ")
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)
    # Limpiar comillas especiales del PDF
    texto = texto.replace("―", '"').replace("‖", '"')
    texto = texto.replace("'", "'").replace("'", "'")
    return texto.strip()

def parsear_rango_versiculos(ref: str) -> tuple:
    """
    Parsea 'Vv. 1, 2' → (1, 2)
    Parsea 'Vv. 1—5' → (1, 5)
    Parsea 'V. 31' → (31, 31)
    Parsea 'Vv. 1—3' → (1, 3)
    Parsea 'Vv. 29, 30' → (29, 30)
    """
    ref = ref.strip()

    # Patrón: Vv. X—Y o Vv. X, Y, Z (rango)
    match_rango = re.search(r'(\d+)[—\-–](\d+)', ref)
    if match_rango:
        return int(match_rango.group(1)), int(match_rango.group(2))

    # Patrón: Vv. X, Y (último número)
    numeros = re.findall(r'\d+', ref)
    if len(numeros) >= 2:
        return int(numeros[0]), int(numeros[-1])
    elif len(numeros) == 1:
        return int(numeros[0]), int(numeros[0])

    return None, None

def extraer_titulo_seccion(titulo_cap: str, ver_inicio: int, ver_fin: int) -> str:
    """
    Del título del capítulo extrae el subtítulo del rango específico.
    Ej: "Versículos 1—3. Dios crea..." → "Dios crea..."
    """
    if not titulo_cap:
        return None

    # Buscar el segmento que corresponde al rango
    patron = rf'\b{ver_inicio}[—,\s].*?\.\s+([^.0-9]+?)(?:\.|$|\d)'
    match = re.search(patron, titulo_cap)
    if match:
        return match.group(1).strip()

    return None

# ============================================================
# PARSER PRINCIPAL
# ============================================================

def extraer_comentarios(pdf_path: str) -> list:
    """Extrae todos los comentarios del PDF de Matthew Henry."""

    comentarios = []
    libro_actual = None
    capitulo_actual = None
    titulo_capitulo_actual = None

    # Patrones de detección
    pat_libro = re.compile(
        r'^(' + '|'.join(re.escape(k) for k in MAPEO_LIBROS.keys()) + r')\s*$',
        re.IGNORECASE
    )
    pat_capitulo = re.compile(r'^CAP[ÍI]TULO\s+([IVXLCDM]+)\s*$', re.IGNORECASE)
    pat_titulo_cap = re.compile(r'^Vers[íi]culos?\s+\d+', re.IGNORECASE)
    pat_comentario = re.compile(r'^(Vv?\.\s*[\d,\s—\-–]+\.)\s*(.+)', re.DOTALL)

    print(f"📖 Leyendo PDF: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        total_paginas = len(pdf.pages)
        print(f"   Total páginas: {total_paginas}")

        texto_acumulado = ""
        pagina_anterior = ""

        for num_pag, page in enumerate(pdf.pages, 1):
            if num_pag % 100 == 0:
                print(f"   Procesando página {num_pag}/{total_paginas}...")

            texto_pag = page.extract_text() or ""

            # Combinar con texto anterior para no perder comentarios que cruzan páginas
            texto_completo = pagina_anterior + "\n" + texto_pag
            lineas = texto_completo.split("\n")

            lineas_nuevas = []
            i = 0
            while i < len(lineas):
                linea = lineas[i].strip()

                # Detectar libro
                match_libro = pat_libro.match(linea.upper())
                if match_libro:
                    libro_actual = MAPEO_LIBROS.get(linea.upper().strip())
                    if not libro_actual:
                        # Intentar con variantes
                        for key in MAPEO_LIBROS:
                            if linea.upper().strip() == key:
                                libro_actual = MAPEO_LIBROS[key]
                                break
                    i += 1
                    continue

                # Detectar capítulo
                match_cap = pat_capitulo.match(linea)
                if match_cap:
                    romano = match_cap.group(1)
                    capitulo_actual = romano_a_arabigo(romano)
                    titulo_capitulo_actual = None
                    i += 1
                    continue

                # Detectar título del capítulo (índice)
                if pat_titulo_cap.match(linea) and capitulo_actual:
                    # Puede continuar en líneas siguientes
                    titulo = linea
                    j = i + 1
                    while j < len(lineas) and lineas[j].strip() and not pat_comentario.match(lineas[j].strip()) and not pat_capitulo.match(lineas[j].strip()):
                        siguiente = lineas[j].strip()
                        if not siguiente:
                            break
                        titulo += " " + siguiente
                        j += 1
                    titulo_capitulo_actual = limpiar_texto(titulo)
                    i = j
                    continue

                # Detectar comentario (Vv. X, Y. o V. X.)
                match_com = pat_comentario.match(linea)
                if match_com and libro_actual and capitulo_actual:
                    ref = match_com.group(1)
                    texto_inicio = match_com.group(2)

                    # Acumular texto del comentario hasta el próximo Vv. o Capítulo
                    texto = texto_inicio
                    j = i + 1
                    while j < len(lineas):
                        sig = lineas[j].strip()
                        if not sig:
                            j += 1
                            continue
                        # Parar si encontramos otro comentario, capítulo o libro
                        if pat_comentario.match(sig) or pat_capitulo.match(sig) or pat_libro.match(sig.upper()):
                            break
                        texto += " " + sig
                        j += 1

                    ver_inicio, ver_fin = parsear_rango_versiculos(ref)
                    if ver_inicio and ver_fin and libro_actual and capitulo_actual:
                        titulo_sec = extraer_titulo_seccion(titulo_capitulo_actual, ver_inicio, ver_fin)
                        comentarios.append({
                            "abreviatura_libro": libro_actual,
                            "capitulo":          capitulo_actual,
                            "titulo_capitulo":   titulo_capitulo_actual,
                            "versiculo_inicio":  ver_inicio,
                            "versiculo_fin":     ver_fin,
                            "titulo_seccion":    titulo_sec,
                            "texto":             limpiar_texto(texto),
                            "autor":             "matthew_henry"
                        })
                    i = j
                    continue

                lineas_nuevas.append(linea)
                i += 1

            # Guardar últimas líneas para la próxima página (comentarios que cruzan páginas)
            pagina_anterior = "\n".join(lineas[-5:]) if len(lineas) > 5 else texto_pag

    return comentarios

# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/extraer_matthew_henry.py <ruta_del_pdf>")
        print('Ejemplo: python3 scripts/extraer_matthew_henry.py "comentario-de-la-biblia-matthew-henry.pdf"')
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"ERROR: No se encontró el archivo {pdf_path}")
        sys.exit(1)

    comentarios = extraer_comentarios(pdf_path)

    # Estadísticas
    libros_cubiertos = len(set(c["abreviatura_libro"] for c in comentarios))
    print(f"\n{'='*50}")
    print(f"✅ Extracción completada")
    print(f"   Comentarios extraídos : {len(comentarios)}")
    print(f"   Libros cubiertos      : {libros_cubiertos}/66")

    # Muestra de los primeros 3
    print(f"\n   Muestra (primeros 3):")
    for c in comentarios[:3]:
        print(f"   [{c['abreviatura_libro'].upper()} {c['capitulo']}:{c['versiculo_inicio']}-{c['versiculo_fin']}] {c['texto'][:80]}...")

    # Guardar JSON
    output_path = Path(pdf_path).parent / "comentarios_matthew_henry.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comentarios, f, ensure_ascii=False, indent=2)

    print(f"\n   Archivo: {output_path}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()