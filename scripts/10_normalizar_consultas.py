import unicodedata
import re


# Normaliza el texto ingresado por el usuario.
def normalizar_texto(texto):
    texto = texto.lower()

    # Separa los caracteres de sus acentos.
    texto = unicodedata.normalize("NFD", texto)

    # Elimina los acentos.
    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    # Elimina signos de puntuación y caracteres especiales.
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)

    # Elimina espacios adicionales.
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


# Programa principal.
def main():
    print("=" * 55)
    print("OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0")
    print("Modulo 1: Normalizacion de consultas")
    print("=" * 55)

    while True:
        pregunta = input("\nEscribe tu pregunta (o 'salir'): ").strip()

        if normalizar_texto(pregunta) == "salir":
            print("\nPrograma finalizado.")
            break

        if not pregunta:
            print("Debes escribir una pregunta.")
            continue

        resultado = normalizar_texto(pregunta)

        print("\nTexto original:   ", pregunta)
        print("Texto normalizado:", resultado)


if __name__ == "__main__":
    main()