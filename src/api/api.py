import requests
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from requests.exceptions import HTTPError
import pandas as pd
import os


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_page(page: int, per_page: int = 50):
    url = "https://api.openbrewerydb.org/v1/breweries"
    params = {"page": page, "per_page": per_page}
    print(f"Tentando buscar página {page}...")
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


try:
    # Loop para buscar todas as páginas
    all_data = []
    page = 1
    while True:
        data = fetch_page(page)
        if not data:  # se vier vazio, acabou
            break
        all_data.extend(data)  # adiciona à lista
        page += 1

    print(f"✅ Total de registros coletados: {len(all_data)}")


except RetryError as re:
    print("❌ Todas as tentativas falharam.")
    if re.last_attempt and re.last_attempt.exception():
        print("👉 Erro final:", re.last_attempt.exception())
except HTTPError as e:
    print("❌ Erro HTTP direto:", e)
except Exception as e:
    print("❌ Outro erro inesperado:", e)


try:
    df = pd.DataFrame(data)
    file_name = "breweries.csv"
    df.to_csv(file_name, index=False)

    file_path = os.path.abspath(file_name)
    print(f"✅ Dados salvos com sucesso em: {file_path}")
except Exception as e:
    print("❌ Falha ao salvar o arquivo.")
    print("👉 Erro:", e)