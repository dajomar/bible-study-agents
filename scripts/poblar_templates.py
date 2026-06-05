#!/usr/bin/env python3
"""
poblar_templates.py
Inserta los 7 templates de planes de estudio bíblico en Supabase.

Tablas que puebla:
  - bible_planes_templates
  - bible_planes_templates_fases
  - bible_planes_templates_sesiones

Uso:
    python3 scripts/poblar_templates.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ============================================================
# CAPÍTULOS POR LIBRO (para calcular duración)
# ============================================================

CAPS = {
    "gn":50,"ex":40,"lv":27,"nm":36,"dt":34,"jos":24,"jue":21,"rt":4,
    "1sam":31,"2sam":24,"1re":22,"2re":25,"1cr":29,"2cr":36,"esd":10,
    "neh":13,"est":10,"job":42,"sal":150,"pr":31,"ec":12,"cnt":8,
    "is":66,"jer":52,"lm":5,"ez":48,"dn":12,"os":14,"jl":3,"am":9,
    "abd":1,"jon":4,"mi":7,"nah":3,"hab":3,"sof":3,"hag":2,"zac":14,
    "mal":4,"mt":28,"mr":16,"lc":24,"jn":21,"hch":28,"ro":16,
    "1co":16,"2co":13,"ga":6,"ef":6,"flp":4,"col":4,"1ts":5,"2ts":3,
    "1ti":6,"2ti":4,"tit":3,"flm":1,"heb":13,"stg":5,"1pe":5,"2pe":3,
    "1jn":5,"2jn":1,"3jn":1,"jud":1,"ap":22,
}

def caps_por_sesion(abrev: str, denso: bool = False) -> int:
    return 2 if denso else 4

def generar_sesiones_libro(abrev: str, caps_sesion: int = 4) -> list:
    """Genera sesiones de N capítulos para un libro completo."""
    total = CAPS[abrev]
    sesiones = []
    cap = 1
    while cap <= total:
        cap_fin = min(cap + caps_sesion - 1, total)
        sesiones.append({
            "abreviatura_libro": abrev,
            "capitulo_inicio": cap,
            "capitulo_fin": cap_fin,
        })
        cap = cap_fin + 1
    return sesiones

def calcular_dias(libros_caps: list) -> int:
    """Calcula días estimados dado lista de (abrev, caps_por_sesion)."""
    total = 0
    for abrev, cps in libros_caps:
        total += len(generar_sesiones_libro(abrev, cps))
    return total

# ============================================================
# DEFINICIÓN DE LOS 7 TEMPLATES
# ============================================================

TEMPLATES = [

    # ----------------------------------------------------------
    # 1. PRIMERA VEZ
    # ----------------------------------------------------------
    {
        "titulo": "Primera vez",
        "descripcion": "Comienza por los Evangelios antes de explorar el resto. Un punto de entrada claro y significativo para quien no sabe por dónde empezar.",
        "para_quien": "Para quien nunca ha leído la Biblia y quiere un punto de entrada claro, accesible y significativo sin abrumarse desde el inicio.",
        "nivel": "principiante",
        "es_completo": False,
        "icono": "ti-seedling",
        "color_acento": "info",
        "recomendado": False,
        "orden": 1,
        "fases": [
            {
                "numero": 1,
                "titulo": "La historia de Jesús",
                "descripcion": "Los cuatro Evangelios narran la vida, muerte y resurrección de Jesús desde perspectivas complementarias.",
                "color_acento": "info",
                "libros": [
                    ("mr", 4), ("mt", 4), ("lc", 4), ("jn", 4),
                ],
            },
            {
                "numero": 2,
                "titulo": "El nacimiento de la iglesia",
                "descripcion": "Hechos narra cómo los seguidores de Jesús llevaron su mensaje al mundo conocido.",
                "color_acento": "warning",
                "libros": [("hch", 4)],
            },
            {
                "numero": 3,
                "titulo": "La fe explicada",
                "descripcion": "Romanos es la carta teológica más completa del Nuevo Testamento — explica el evangelio de forma sistemática.",
                "color_acento": "success",
                "libros": [("ro", 4)],
            },
        ],
    },

    # ----------------------------------------------------------
    # 2. DEVOCIONAL DIARIO
    # ----------------------------------------------------------
    {
        "titulo": "Devocional diario",
        "descripcion": "Un camino corto y profundo por los libros de sabiduría. Ideal para leer en paralelo con cualquier otro plan de estudio.",
        "para_quien": "Para quien quiere una lectura diaria de reflexión personal, oración y sabiduría práctica para la vida cotidiana.",
        "nivel": "principiante",
        "es_completo": False,
        "icono": "ti-heart",
        "color_acento": "danger",
        "recomendado": False,
        "orden": 2,
        "fases": [
            {
                "numero": 1,
                "titulo": "Salmos — oración y alabanza",
                "descripcion": "150 poemas que cubren toda la gama de la experiencia humana — alegría, dolor, duda, gratitud y adoración.",
                "color_acento": "danger",
                "libros": [("sal", 4)],
            },
            {
                "numero": 2,
                "titulo": "Proverbios — sabiduría práctica",
                "descripcion": "Consejos concretos para vivir con integridad, justicia y discernimiento en cada área de la vida.",
                "color_acento": "warning",
                "libros": [("pr", 4)],
            },
        ],
    },

    # ----------------------------------------------------------
    # 3. LA VIDA DE JESÚS
    # ----------------------------------------------------------
    {
        "titulo": "La vida de Jesús",
        "descripcion": "Recorre la vida de Jesús desde cuatro perspectivas distintas. Cada Evangelio revela una dimensión única de su persona.",
        "para_quien": "Para quien quiere conocer a Jesús en profundidad — su carácter, sus milagros, sus relaciones y su misión.",
        "nivel": "principiante",
        "es_completo": False,
        "icono": "ti-user",
        "color_acento": "warning",
        "recomendado": False,
        "orden": 3,
        "fases": [
            {
                "numero": 1,
                "titulo": "Marcos — el Jesús que actúa",
                "descripcion": "El Evangelio más corto y dinámico. Jesús en acción — milagros, confrontaciones y movimiento constante.",
                "color_acento": "info",
                "libros": [("mr", 4)],
            },
            {
                "numero": 2,
                "titulo": "Mateo — el Jesús que cumple",
                "descripcion": "Escrito para lectores judíos, muestra cómo Jesús cumple las profecías del Antiguo Testamento.",
                "color_acento": "warning",
                "libros": [("mt", 4)],
            },
            {
                "numero": 3,
                "titulo": "Lucas — el Jesús que incluye",
                "descripcion": "El Evangelio más humano. Lucas destaca la compasión de Jesús por los pobres, las mujeres y los excluidos.",
                "color_acento": "success",
                "libros": [("lc", 4)],
            },
            {
                "numero": 4,
                "titulo": "Juan — el Jesús que es Dios",
                "descripcion": "El Evangelio teológico. Juan explora la naturaleza divina de Jesús con señales, discursos y el famoso prólogo.",
                "color_acento": "danger",
                "libros": [("jn", 4)],
            },
        ],
    },

    # ----------------------------------------------------------
    # 4. LAS ENSEÑANZAS DE JESÚS
    # ----------------------------------------------------------
    {
        "titulo": "Las enseñanzas de Jesús",
        "descripcion": "Un recorrido enfocado en lo que Jesús enseñó — parábolas, el Sermón del Monte y el mandamiento del amor.",
        "para_quien": "Para quien quiere entender el mensaje central de Jesús — qué dijo, qué quiso decir y cómo aplicarlo hoy.",
        "nivel": "principiante",
        "es_completo": False,
        "icono": "ti-message-circle",
        "color_acento": "success",
        "recomendado": False,
        "orden": 4,
        "fases": [
            {
                "numero": 1,
                "titulo": "Mateo — el gran maestro",
                "descripcion": "El Sermón del Monte, las parábolas del reino y los grandes discursos de Jesús sobre el fin de los tiempos.",
                "color_acento": "info",
                "libros": [("mt", 4)],
            },
            {
                "numero": 2,
                "titulo": "Lucas — parábolas de gracia",
                "descripcion": "El hijo pródigo, el buen samaritano, la oveja perdida — las parábolas más amadas de Jesús.",
                "color_acento": "warning",
                "libros": [("lc", 4)],
            },
            {
                "numero": 3,
                "titulo": "Juan — el mandamiento del amor",
                "descripcion": "Los discursos del aposento alto, la oración sacerdotal y la enseñanza sobre el Espíritu Santo.",
                "color_acento": "success",
                "libros": [("jn", 4)],
            },
        ],
    },

    # ----------------------------------------------------------
    # 5. JESÚS Y LA IGLESIA
    # ----------------------------------------------------------
    {
        "titulo": "Jesús y la iglesia",
        "descripcion": "De la vida de Jesús al nacimiento de la iglesia y las cartas que formaron la fe cristiana. El Nuevo Testamento completo.",
        "para_quien": "Para quien quiere entender no solo a Jesús sino cómo su mensaje transformó el mundo a través de sus seguidores.",
        "nivel": "intermedio",
        "es_completo": False,
        "icono": "ti-flame",
        "color_acento": "info",
        "recomendado": False,
        "orden": 5,
        "fases": [
            {
                "numero": 1,
                "titulo": "Los Evangelios",
                "descripcion": "La vida, muerte y resurrección de Jesús desde cuatro perspectivas complementarias.",
                "color_acento": "info",
                "libros": [("mr", 4), ("mt", 4), ("lc", 4), ("jn", 4)],
            },
            {
                "numero": 2,
                "titulo": "El nacimiento de la iglesia",
                "descripcion": "Hechos narra la expansión del evangelio desde Jerusalén hasta Roma.",
                "color_acento": "warning",
                "libros": [("hch", 4)],
            },
            {
                "numero": 3,
                "titulo": "Las cartas de Pablo",
                "descripcion": "Romanos, Corintios, Gálatas y las cartas a las iglesias que Pablo fundó.",
                "color_acento": "success",
                "libros": [
                    ("ro", 4), ("1co", 4), ("2co", 4), ("ga", 4),
                    ("ef", 4), ("flp", 4), ("col", 4), ("1ts", 4),
                    ("2ts", 4), ("1ti", 4), ("2ti", 4), ("tit", 4),
                    ("flm", 4),
                ],
            },
            {
                "numero": 4,
                "titulo": "Las cartas generales",
                "descripcion": "Hebreos, Santiago, Pedro, Juan y Judas — cartas dirigidas a la iglesia en general.",
                "color_acento": "danger",
                "libros": [
                    ("heb", 4), ("stg", 4), ("1pe", 4), ("2pe", 4),
                    ("1jn", 4), ("2jn", 4), ("3jn", 4), ("jud", 4),
                ],
            },
            {
                "numero": 5,
                "titulo": "El final de la historia",
                "descripcion": "Apocalipsis — la visión de Juan sobre el triunfo final de Dios.",
                "color_acento": "info",
                "libros": [("ap", 2)],
            },
        ],
    },

    # ----------------------------------------------------------
    # 6. LA GRAN HISTORIA (7 fases)
    # ----------------------------------------------------------
    {
        "titulo": "La gran historia",
        "descripcion": "Un recorrido pedagógico completo que conecta historia, poesía, profecía y el Nuevo Testamento en un solo hilo narrativo.",
        "para_quien": "Para quien quiere entender la Biblia como un todo — cómo los 66 libros cuentan una sola historia desde la creación hasta el Apocalipsis.",
        "nivel": "completo",
        "es_completo": True,
        "icono": "ti-map-2",
        "color_acento": "warning",
        "recomendado": True,
        "orden": 6,
        "fases": [
            {
                "numero": 1,
                "titulo": "Historia principal",
                "descripcion": "La creación, Abraham, Moisés, la salida de Egipto, los jueces, la monarquía y el exilio. El hilo principal del Antiguo Testamento.",
                "color_acento": "info",
                "libros": [
                    ("gn",4),("ex",4),("jos",4),("jue",4),("rt",4),
                    ("1sam",4),("2sam",4),("1re",4),("2re",4),
                    ("1cr",4),("2cr",4),("esd",4),("neh",4),("est",4),
                ],
            },
            {
                "numero": 2,
                "titulo": "Evangelios y Hechos",
                "descripcion": "La vida de Jesús desde cuatro perspectivas y el nacimiento de la iglesia.",
                "color_acento": "warning",
                "libros": [("mr",4),("mt",4),("lc",4),("jn",4),("hch",4)],
            },
            {
                "numero": 3,
                "titulo": "Volver al Antiguo Testamento",
                "descripcion": "Con el contexto de Jesús, las leyes de Levítico, Números y Deuteronomio adquieren un sentido nuevo.",
                "color_acento": "success",
                "libros": [("lv",4),("nm",4),("dt",4)],
            },
            {
                "numero": 4,
                "titulo": "Libros poéticos y sabiduría",
                "descripcion": "Job, Salmos, Proverbios, Eclesiastés y Cantares — la dimensión lírica y contemplativa de la fe.",
                "color_acento": "danger",
                "libros": [("job",4),("sal",4),("pr",4),("ec",4),("cnt",4)],
            },
            {
                "numero": 5,
                "titulo": "Los profetas",
                "descripcion": "Mayores y menores — estudiados junto con la época histórica en que profetizaron.",
                "color_acento": "secondary",
                "libros": [
                    ("is",4),("jer",4),("lm",4),("ez",2),("dn",4),
                    ("os",4),("jl",4),("am",4),("abd",4),("jon",4),
                    ("mi",4),("nah",4),("hab",4),("sof",4),("hag",4),
                    ("zac",4),("mal",4),
                ],
            },
            {
                "numero": 6,
                "titulo": "Cartas del Nuevo Testamento",
                "descripcion": "Las cartas que formaron la teología cristiana.",
                "color_acento": "info",
                "libros": [
                    ("ro",4),("1co",4),("2co",4),("ga",4),("ef",4),
                    ("flp",4),("col",4),("1ts",4),("2ts",4),("1ti",4),
                    ("2ti",4),("tit",4),("flm",4),("heb",4),("stg",4),
                    ("1pe",4),("2pe",4),("1jn",4),("2jn",4),("3jn",4),
                    ("jud",4),
                ],
            },
            {
                "numero": 7,
                "titulo": "Apocalipsis",
                "descripcion": "El libro más rico en referencias bíblicas — ahora con todo el contexto necesario.",
                "color_acento": "warning",
                "libros": [("ap",2)],
            },
        ],
    },

    # ----------------------------------------------------------
    # 7. CRONOLÓGICO
    # ----------------------------------------------------------
    {
        "titulo": "Cronológico",
        "descripcion": "Lee la Biblia como una línea de tiempo. Cada libro en el momento histórico en que ocurrió, no en el orden del canon.",
        "para_quien": "Para quien ya conoce la Biblia y quiere entenderla desde su contexto histórico real — cuándo fue escrito cada libro y qué pasaba en ese momento.",
        "nivel": "intermedio",
        "es_completo": True,
        "icono": "ti-clock",
        "color_acento": "success",
        "recomendado": False,
        "orden": 7,
        "fases": [
            {
                "numero": 1,
                "titulo": "Los orígenes (~2000 a.C.)",
                "descripcion": "La creación, el diluvio, Abraham, Isaac, Jacob y José. Los patriarcas y el inicio del pueblo de Israel.",
                "color_acento": "info",
                "libros": [("gn",4),("job",4)],
            },
            {
                "numero": 2,
                "titulo": "Moisés y la Ley (~1400 a.C.)",
                "descripcion": "El éxodo de Egipto, las leyes del Sinaí y los 40 años en el desierto.",
                "color_acento": "warning",
                "libros": [("ex",4),("lv",4),("nm",4),("dt",4)],
            },
            {
                "numero": 3,
                "titulo": "La conquista y los jueces (~1400–1050 a.C.)",
                "descripcion": "Israel entra a Canaán, se reparte la tierra y vive el ciclo de apostasía y restauración bajo los jueces.",
                "color_acento": "success",
                "libros": [("jos",4),("jue",4),("rt",4)],
            },
            {
                "numero": 4,
                "titulo": "La monarquía unida (~1050–930 a.C.)",
                "descripcion": "Saúl, David y Salomón. El reino en su apogeo y la escritura de los Salmos y Proverbios.",
                "color_acento": "danger",
                "libros": [("1sam",4),("2sam",4),("1re",4),("sal",4),("pr",4),("ec",4),("cnt",4)],
            },
            {
                "numero": 5,
                "titulo": "El reino dividido (~930–722 a.C.)",
                "descripcion": "Israel y Judá separados. Los primeros profetas advierten sobre el juicio que viene.",
                "color_acento": "info",
                "libros": [("2re",4),("1cr",4),("2cr",4),("os",4),("jl",4),("am",4),("jon",4),("mi",4),("is",4)],
            },
            {
                "numero": 6,
                "titulo": "La caída y el exilio (~722–539 a.C.)",
                "descripcion": "Asiria destruye Israel. Babilonia destruye Judá. Los profetas del exilio hablan de esperanza.",
                "color_acento": "warning",
                "libros": [("nah",4),("hab",4),("sof",4),("jer",4),("lm",4),("ez",2),("dn",4),("abd",4)],
            },
            {
                "numero": 7,
                "titulo": "El regreso del exilio (~539–400 a.C.)",
                "descripcion": "Persia permite el regreso. Israel reconstruye el templo y los muros de Jerusalén.",
                "color_acento": "success",
                "libros": [("hag",4),("zac",4),("esd",4),("neh",4),("est",4),("mal",4)],
            },
            {
                "numero": 8,
                "titulo": "El cumplimiento — Jesús (~4 a.C.–30 d.C.)",
                "descripcion": "Los cuatro Evangelios narran la vida, muerte y resurrección de Jesús.",
                "color_acento": "danger",
                "libros": [("mr",4),("mt",4),("lc",4),("jn",4)],
            },
            {
                "numero": 9,
                "titulo": "La iglesia primitiva (~30–100 d.C.)",
                "descripcion": "Hechos y las cartas de Pablo escritas durante sus viajes misioneros.",
                "color_acento": "info",
                "libros": [
                    ("hch",4),("stg",4),("ga",4),("1ts",4),("2ts",4),
                    ("1co",4),("2co",4),("ro",4),("ef",4),("flp",4),
                    ("col",4),("flm",4),("1ti",4),("2ti",4),("tit",4),
                    ("1pe",4),("heb",4),("2pe",4),("jud",4),
                    ("1jn",4),("2jn",4),("3jn",4),("ap",2),
                ],
            },
        ],
    },

]

# ============================================================
# CARGA EN SUPABASE
# ============================================================

def poblar_templates():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Verificar si ya están cargados
    existentes = supabase.table("bible_planes_templates").select("id", count="exact").execute()
    if existentes.count and existentes.count > 0:
        print(f"Ya existen {existentes.count} templates. Abortando.")
        print("Si deseas recargar, elimina los registros primero.")
        sys.exit(0)

    print("📚 Insertando templates de planes de estudio...\n")

    total_sesiones = 0

    for t in TEMPLATES:
        # Calcular duración total
        dias = sum(
            len(generar_sesiones_libro(abrev, cps))
            for fase in t["fases"]
            for abrev, cps in fase["libros"]
        )

        # Insertar template
        template_db = supabase.table("bible_planes_templates").insert({
            "titulo":                 t["titulo"],
            "descripcion":            t["descripcion"],
            "para_quien":             t["para_quien"],
            "nivel":                  t["nivel"],
            "es_completo":            t["es_completo"],
            "duracion_estimada_dias": dias,
            "icono":                  t["icono"],
            "color_acento":           t["color_acento"],
            "recomendado":            t["recomendado"],
            "creado_por":             "sistema",
            "activo":                 True,
            "orden":                  t["orden"],
        }).execute().data[0]

        id_template = template_db["id"]
        print(f"  ✅ [{t['orden']}] {t['titulo']} — {dias} días")

        for fase in t["fases"]:
            # Insertar fase
            fase_db = supabase.table("bible_planes_templates_fases").insert({
                "id_template":  id_template,
                "numero":       fase["numero"],
                "titulo":       fase["titulo"],
                "descripcion":  fase["descripcion"],
                "color_acento": fase["color_acento"],
            }).execute().data[0]

            id_fase = fase_db["id"]

            # Generar y insertar sesiones de la fase
            sesiones = []
            orden = 1
            for abrev, cps in fase["libros"]:
                for s in generar_sesiones_libro(abrev, cps):
                    sesiones.append({
                        "id_fase":          id_fase,
                        "orden":            orden,
                        "abreviatura_libro": s["abreviatura_libro"],
                        "capitulo_inicio":  s["capitulo_inicio"],
                        "capitulo_fin":     s["capitulo_fin"],
                    })
                    orden += 1

            # Insertar en lotes
            for i in range(0, len(sesiones), 500):
                supabase.table("bible_planes_templates_sesiones").insert(
                    sesiones[i:i+500]
                ).execute()

            total_sesiones += len(sesiones)
            print(f"     Fase {fase['numero']}: {fase['titulo']} — {len(sesiones)} sesiones")

    print(f"\n{'='*50}")
    print(f"✅ Templates cargados exitosamente")
    print(f"   Templates  : {len(TEMPLATES)}")
    print(f"   Sesiones   : {total_sesiones}")
    print(f"{'='*50}")


if __name__ == "__main__":
    poblar_templates()