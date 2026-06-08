"""
Konfiguracja aplikacji Pillar Two / GloBE.
Przed uruchomieniem w środowisku produkcyjnym skonsultuj z administratorem IT.
"""

import os

# ── Ścieżki ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
DRAFTS_DIR  = os.path.join(BASE_DIR, "drafts")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

GLB_Z2_SCHEMA = os.path.join(SCHEMAS_DIR, "GLB_Z2_schemat.xsd")
GIR_SCHEMA    = os.path.join(SCHEMAS_DIR, "GIR_schemat.xsd")

# ── Namespaces XML ───────────────────────────────────────────────────────────
GLBZ2_NS = "http://crd.gov.pl/wzor/2025/11/07/13986/"
GIR_NS   = "http://globe.mf.gov.pl/2025/03/31/03311/"

# ── Submission adapter – konfiguracja integracji z MF ───────────────────────
# Ustaw SUBMISSION_ENDPOINT i SUBMISSION_API_KEY gdy posiadasz dane dostępowe.
SUBMISSION_ENDPOINT = os.environ.get("MF_SUBMISSION_ENDPOINT", "")
SUBMISSION_API_KEY  = os.environ.get("MF_API_KEY", "")

# Ścieżka do certyfikatu / klucza do podpisu (np. kwalifikowany podpis elektroniczny)
CERT_PATH = os.environ.get("CERT_PATH", "")
CERT_KEY_PATH = os.environ.get("CERT_KEY_PATH", "")

# ── Flagi bezpieczeństwa ─────────────────────────────────────────────────────
ENABLE_SUBMISSION = False   # Zmień na True dopiero po skonfigurowaniu endpointu i certyfikatu
LOG_SENSITIVE_DATA = False  # NIGDY nie ustawiaj na True w środowisku produkcyjnym

# ── Wersja aplikacji ─────────────────────────────────────────────────────────
APP_VERSION = "0.1.0-MVP"
