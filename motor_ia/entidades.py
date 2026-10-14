
import psycopg2
from getpass import getpass


# Establecer conexion con PostgreSQL.
def conectar_bd():
    contrasena = getpass("Contraseña de PostgreSQL: ")

    conexion = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="oferta_educativa",
        user="postgres",
        password=contrasena,
        connect_timeout=5
    )

    return conexion


# Consultar los catalogos necesarios para el motor de IA.
def consultar_catalogos(conexion):
    consultas = {
        "instituciones": """
            SELECT id_institucion, nombre
            FROM catalogo.institucion
            ORDER BY nombre
        """,
        "programas": """
            SELECT id_programa, nombre
            FROM catalogo.programa_academico
            ORDER BY nombre
        """,
        "modalidades": """
            SELECT id_modalidad, nombre
            FROM catalogo.modalidad
            ORDER BY nombre
        """
    }

    with conexion.cursor() as cursor:
        for nombre, sql in consultas.items():
            cursor.execute(sql)
            registros = cursor.fetchall()
            print(f"{nombre}: {len(registros)} registros")


# Normalizar texto para comparar modalidades.
def normalizar_texto(texto):
    import unicodedata
    import re

    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


# Identificar la modalidad mencionada en una pregunta.
def extraer_modalidad(pregunta):
    texto = normalizar_texto(pregunta)

    equivalencias = {
        "NO ESCOLARIZADA": [
            "no escolarizada",
            "no escolarizadas",
            "a distancia",
            "en linea",
            "virtual"
        ],
        "MIXTA": [
            "mixta",
            "mixtas",
            "semipresencial",
            "semipresenciales"
        ],
        "ESCOLARIZADA": [
            "escolarizada",
            "escolarizadas",
            "presencial",
            "presenciales"
        ]
    }

    for modalidad, expresiones in equivalencias.items():
        for expresion in expresiones:
            if f" {expresion} " in f" {texto} ":
                return modalidad

    return None


# Obtener las instituciones registradas en PostgreSQL.
def cargar_instituciones(conexion):
    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT id_institucion, nombre
            FROM catalogo.institucion
            ORDER BY LENGTH(nombre) DESC
        """)

        return cursor.fetchall()


# Identificar una institucion mencionada en la pregunta.
def extraer_institucion(pregunta, instituciones):
    texto = normalizar_texto(pregunta)

    for id_institucion, nombre in instituciones:
        nombre_normalizado = normalizar_texto(nombre)

        if f" {nombre_normalizado} " in f" {texto} ":
            return {
                "id_institucion": id_institucion,
                "nombre": nombre
            }

    return None


# Obtener los programas registrados en PostgreSQL.
def cargar_programas(conexion):
    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT id_programa, nombre
            FROM catalogo.programa_academico
            ORDER BY LENGTH(nombre) DESC
        """)

        return cursor.fetchall()


# Identificar el programa mencionado en la pregunta.
def extraer_programa(pregunta, programas):
    texto = normalizar_texto(pregunta)
    coincidencias = []

    for id_programa, nombre in programas:
        nombre_normalizado = normalizar_texto(nombre)

        # Eliminar el prefijo EN cuando corresponda.
        if nombre_normalizado.startswith("en "):
            nombre_busqueda = nombre_normalizado[3:]
        else:
            nombre_busqueda = nombre_normalizado

        if f" {nombre_busqueda} " in f" {texto} ":
            coincidencias.append({
                "id_programa": id_programa,
                "nombre": nombre,
                "longitud": len(nombre_busqueda)
            })

    if coincidencias:
        coincidencias.sort(
            key=lambda programa: programa["longitud"],
            reverse=True
        )

        return coincidencias[0]

    return None


def main():
    try:
        with conectar_bd() as conexion:
            print("\nConexion establecida con PostgreSQL.")
            consultar_catalogos(conexion)
            instituciones = cargar_instituciones(conexion)
            programas = cargar_programas(conexion)

            while True:
                pregunta = input(
                    "\nEscribe tu pregunta (o 'salir'): "
                ).strip()

                if normalizar_texto(pregunta) == "salir":
                    print("Programa finalizado.")
                    break

                if not pregunta:
                    print("Debes escribir una pregunta.")
                    continue

                modalidad = extraer_modalidad(pregunta)

                if modalidad:
                    print("Modalidad detectada:", modalidad)
                else:
                    print("No se identifico ninguna modalidad.")

                institucion = extraer_institucion(pregunta, instituciones)

                if institucion:
                    print("Institucion detectada:", institucion["nombre"])
                    print("ID institucion:", institucion["id_institucion"])
                else:
                    print("No se identifico ninguna institucion.")

                programa = extraer_programa(pregunta, programas)

                if programa:
                    print("Programa detectado:", programa["nombre"])
                    print("ID programa:", programa["id_programa"])
                else:
                    print("No se identifico ningun programa.")

    except psycopg2.Error as error:
        print(f"\nError de PostgreSQL: {error}")


if __name__ == "__main__":
    main()
