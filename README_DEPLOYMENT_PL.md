# Wdrożenie demo – Streamlit Community Cloud

Cel: szybkie demo webowe bez danych klienckich i bez instalowania Pythona na laptopie.

## 1. GitHub
1. Wejdź na github.com i utwórz nowe repozytorium, np. `pillar2-tool-demo`.
2. Ustaw repo jako `private`, jeżeli nie chcesz pokazywać kodu publicznie.
3. Wgraj całą zawartość folderu `pillar2_tool` do repozytorium.

W repozytorium powinny być widoczne m.in.:
- `app/main.py`
- `requirements.txt`
- `schemas/GLB_Z2_schemat.xsd`
- `schemas/GIR_schemat.xsd`
- `.streamlit/config.toml`

## 2. Streamlit Cloud
1. Wejdź na streamlit.io/cloud.
2. Zaloguj się kontem GitHub.
3. Kliknij `New app`.
4. Wybierz repozytorium `pillar2-tool-demo`.
5. Jako Main file path wpisz:

```text
app/main.py
```

6. Kliknij `Deploy`.

Po chwili dostaniesz adres w rodzaju:

```text
https://pillar2-tool-demo.streamlit.app
```

## 3. Ważne ograniczenia demo
- Nie wpisuj danych klienckich ani danych produkcyjnych.
- Wysyłka do MF jest placeholderem i nie działa produkcyjnie.
- Demo służy wyłącznie pokazaniu UX, generowania XML i kierunku rozwiązania.

# Docelowo – Azure

Rekomendowany wariant produkcyjny:
- Azure App Service albo Azure Container Apps,
- prywatne repozytorium Azure DevOps / GitHub Enterprise,
- uwierzytelnianie przez Entra ID,
- storage w Azure Blob / SQL,
- Key Vault dla sekretów i certyfikatów,
- logowanie bez danych wrażliwych,
- później integracja podpisu i kanału MF.
