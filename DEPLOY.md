# Guide de déploiement

## Architecture en production

```
[Vercel] Frontend React  →  [Railway] Backend FastAPI + SQLite
```

---

## 1. Préparer un dépôt Git

Si ce n'est pas déjà fait :

```bash
cd /Users/jonathanmorel/Applications/real-estate-app
git init
git add .
git commit -m "Initial commit"
```

Puis crée un dépôt sur GitHub et pousse :

```bash
git remote add origin https://github.com/TON_COMPTE/immobilier-normandie.git
git push -u origin main
```

---

## 2. Déployer le Backend sur Railway

1. Va sur [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Sélectionne ton dépôt
3. Railway détecte automatiquement le `railway.toml` et le `Dockerfile`
4. Dans les **Settings** du service → **Variables**, ajoute :

   | Variable | Valeur |
   |----------|--------|
   | `DATABASE_PATH` | `/data/real_estate.db` |
   | `CORS_ORIGINS` | `https://ton-app.vercel.app` *(à compléter après le déploiement Vercel)* |

5. Dans **Settings** → **Volumes**, crée un volume monté sur `/data`
6. Note l'URL publique du backend, ex : `https://immobilier-normandie-prod.up.railway.app`

---

## 3. Déployer le Frontend sur Vercel

1. Va sur [vercel.com](https://vercel.com) → **New Project** → importe ton dépôt GitHub
2. Configure le projet :
   - **Root Directory** : `frontend`
   - **Build Command** : `npm run build`
   - **Output Directory** : `dist`
3. Dans **Environment Variables**, ajoute :

   | Variable | Valeur |
   |----------|--------|
   | `VITE_API_URL` | `https://immobilier-normandie-prod.up.railway.app/api` |

4. Clique **Deploy**
5. Note l'URL Vercel, ex : `https://immobilier-normandie.vercel.app`

---

## 4. Finaliser la configuration CORS

Retourne sur Railway → Variables → mets à jour `CORS_ORIGINS` avec l'URL Vercel :

```
CORS_ORIGINS=https://immobilier-normandie.vercel.app
```

Redémarre le service Railway.

---

## 5. Vérifier que tout fonctionne

1. Ouvre `https://immobilier-normandie.vercel.app`
2. L'app doit charger (carte + filtres)
3. Lance un scraping depuis l'interface pour peupler la base
4. Partage l'URL Vercel avec tes utilisateurs !

---

## Notes importantes

- **SQLite sur Railway** : la DB est persistante grâce au volume `/data`. Si le service Railway est supprimé, les données sont perdues. Pense à exporter la DB régulièrement.
- **Playwright sur Railway** : le build Docker est plus long (installation de Chromium ~300MB). C'est normal.
- **Plan gratuit Railway** : 500h d'exécution/mois. Pour un usage personnel c'est suffisant, sinon passe au plan Hobby (5$/mois).
- **Scraping** : le scraping (PAP, BienIci) fonctionne depuis Railway car Playwright est inclus dans le Docker.
