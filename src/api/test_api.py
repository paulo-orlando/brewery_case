import requests
import time
import csv

base_url = "https://api.openbrewerydb.org/v1/breweries"
per_page = 200
page = 1
all_breweries = []

while True:
    params = {
        "page": page,
        "per_page": per_page
    }
    resp = requests.get(base_url, params=params)
    data = resp.json()
    if not data:
        break
    all_breweries.extend(data)
    print(f"Página {page}, {len(data)} registros")
    page += 1
    time.sleep(0.2)  # para evitar sobrecarregar o serviço

# Depois você pode salvar em CSV ou JSON:
import pandas as pd
df = pd.DataFrame(all_breweries)
output_path = r"C:\Users\victo\OneDrive\Documentos\Brewery\breweries_all.csv"
df.to_csv(output_path, index=False)

print(f"✅ Importação concluída! Arquivo salvo como {output_path}")