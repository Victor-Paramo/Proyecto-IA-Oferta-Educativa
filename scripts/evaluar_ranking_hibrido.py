"""Experimento offline: ranking MiniLM frente a MiniLM + TF-IDF de caracteres.

No modifica PostgreSQL ni app.py. Las etiquetas son propuestas de evaluación,
no datos de entrenamiento ni verdades definitivas.
"""
import csv
import math
import re
import unicodedata
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / 'datos' / 'evaluacion_semantica_escala_0_2.csv'
SALIDA = RAIZ / 'datos' / 'comparacion_ranking_hibrido.csv'
PESO_MINILM = 0.85  # Valor experimental, no parametro definitivo.


def normalizar(texto):
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                    if unicodedata.category(c) != 'Mn')
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', texto).split())


def ndcg(ordenados):
    """NDCG@5 con relevancia graduada; indefinido cuando los cinco son 0."""
    etiquetas = [int(f['pertinencia_0_2']) for f in ordenados]
    def dcg(valores):
        return sum((2 ** etiqueta - 1) / math.log2(i + 2)
                   for i, etiqueta in enumerate(valores))
    ideal = dcg(sorted(etiquetas, reverse=True))
    return dcg(etiquetas) / ideal if ideal else None


def principal():
    if not ENTRADA.is_file():
        raise SystemExit(f'No se encontro el CSV: {ENTRADA}')

    with ENTRADA.open('r', encoding='utf-8-sig', newline='') as archivo:
        filas = list(csv.DictReader(archivo))
    if len(filas) != 60:
        raise SystemExit(f'Se esperaban 60 filas; llegaron {len(filas)}')

    # Un vocabulario de nombres que aparecen en este diagnostico solamente.
    # Esto es un experimento offline, no el catalogo completo de produccion.
    vectorizador = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5))
    corpus = [normalizar(f['programa']) for f in filas]
    preguntas = [normalizar(f['pregunta']) for f in filas]
    matriz = vectorizador.fit_transform(corpus + preguntas)
    corte = len(filas)
    similitudes = matriz[:corte].multiply(matriz[corte:]).sum(axis=1)
    similitudes = similitudes.A1 if hasattr(similitudes, 'A1') else similitudes.toarray().ravel()

    por_caso = {}
    for fila, similitud_lexica in zip(filas, similitudes):
        fila['similitud_lexica'] = float(similitud_lexica)
        fila['puntuacion_hibrida'] = (
            PESO_MINILM * float(fila['similitud'])
            + (1 - PESO_MINILM) * float(similitud_lexica)
        )
        por_caso.setdefault(fila['caso'], []).append(fila)

    print('Comparacion de rankings - diagnostico exploratorio')
    print('Peso MiniLM:', PESO_MINILM, '| Peso lexical:', 1 - PESO_MINILM)
    print('NOTA: Esto NO valida la pertinencia ni decide que preguntas rechazar.\n')
    for caso, grupo in por_caso.items():
        original = sorted(grupo, key=lambda f: int(f['posicion']))
        combinado = sorted(grupo, key=lambda f: f['puntuacion_hibrida'], reverse=True)
        a = ndcg(original)
        b = ndcg(combinado)
        fmt = lambda valor: 'N/A (sin pertinentes)' if valor is None else f'{valor:.3f}'
        print(f'{caso:16s} | MiniLM NDCG@5: {fmt(a):>22} | Hibrido: {fmt(b):>22}')
        for nueva_pos, fila in enumerate(combinado, 1):
            fila['posicion_hibrida'] = nueva_pos

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    columnas = list(filas[0])
    with SALIDA.open('w', encoding='utf-8-sig', newline='') as archivo:
        salida = csv.DictWriter(archivo, fieldnames=columnas)
        salida.writeheader()
        salida.writerows(filas)
    print('\nResultados guardados en:', SALIDA)
    print('No se modificaron los modelos, la base de datos ni app.py.')


if __name__ == '__main__':
    principal()
