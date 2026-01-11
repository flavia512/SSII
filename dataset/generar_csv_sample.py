import os
import csv

categorias = ['finanzas', 'gobiernos', 'tecnologia']
base_dir = os.path.join(os.path.dirname(__file__), '..', 'noticias')
output_csv = os.path.join(os.path.dirname(__file__), 'noticias_sample_10x3.csv')

rows = []
for cat in categorias:
    folder = os.path.join(base_dir, cat, 'noticias')
    if not os.path.exists(folder):
        continue
    archivos = [f for f in os.listdir(folder) if f.endswith('.txt')]
    for archivo in archivos[:10]:
        path = os.path.join(folder, archivo)
        with open(path, encoding='utf-8') as f:
            line = f.readline().strip()
            campos = line.split(';')
            if len(campos) >= 3:
                fecha, titulo, *contenido = campos
                contenido = ';'.join(contenido)
                rows.append([cat, titulo, contenido, fecha])

with open(output_csv, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['categoria', 'titulo', 'contenido', 'fecha'])
    writer.writerows(rows)

print(f"CSV creado en: {output_csv}")
