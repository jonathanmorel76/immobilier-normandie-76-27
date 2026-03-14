#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Chercher Node.js dans les emplacements courants
for NODE_SEARCH in "/usr/local/bin" "/opt/homebrew/bin" "$HOME/bin" "/tmp/node-v22.12.0-darwin-x64/bin"; do
  if [ -x "$NODE_SEARCH/node" ]; then
    export PATH="$NODE_SEARCH:$PATH"
    break
  fi
done

echo "========================================"
echo "  Immobilier Normandie – Démarrage"
echo "========================================"

# ── Backend ──────────────────────────────────
echo ""
echo "[1/2] Démarrage du backend Python..."

# Créer le venv si absent
if [ ! -d "$BACKEND_DIR/.venv" ]; then
  echo "  Création de l'environnement Python..."
  python3 -m venv "$BACKEND_DIR/.venv"
fi

# Installer les dépendances si nécessaire
if ! "$BACKEND_DIR/.venv/bin/python" -c "import fastapi" 2>/dev/null; then
  echo "  Installation des dépendances Python..."
  "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt" -q
fi

# Installer Playwright si nécessaire
if ! "$BACKEND_DIR/.venv/bin/python" -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
  echo "  Installation de Playwright..."
  "$BACKEND_DIR/.venv/bin/pip" install playwright -q
fi

# Vérifier que Chromium est installé
if ! "$BACKEND_DIR/.venv/bin/python" -m playwright install chromium 2>/dev/null | grep -q "already"; then
  echo "  Téléchargement de Chromium pour Playwright..."
  "$BACKEND_DIR/.venv/bin/python" -m playwright install chromium
fi

# Lancer le backend en arrière-plan
cd "$BACKEND_DIR"
"$BACKEND_DIR/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  Backend lancé (PID: $BACKEND_PID) → http://localhost:8000"
echo "  Documentation API : http://localhost:8000/docs"

# ── Frontend ─────────────────────────────────
echo ""
echo "[2/2] Démarrage du frontend React..."

# Vérifier Node.js
if ! command -v node &>/dev/null; then
  echo ""
  echo "  ⚠️  Node.js non trouvé !"
  echo "  Installez-le depuis https://nodejs.org (version LTS recommandée)"
  echo ""
  echo "  Le backend tourne toujours sur http://localhost:8000"
  echo "  Relancez ce script après avoir installé Node.js."
  wait $BACKEND_PID
  exit 0
fi

cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
  echo "  Installation des dépendances npm..."
  npm install
fi

node ./node_modules/.bin/vite --host &
FRONTEND_PID=$!
echo "  Frontend lancé (PID: $FRONTEND_PID) → http://localhost:5173"

echo ""
echo "========================================"
echo "  Application prête !"
echo "  Ouvrez : http://localhost:5173"
echo "  Ctrl+C pour arrêter"
echo "========================================"

# Attendre et gérer l'arrêt propre
trap "echo ''; echo 'Arrêt...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
