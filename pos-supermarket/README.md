# POS Supermarket (Offline)

Logiciel de caisse offline en Python avec architecture en couches:

- UI Layer (PyQt6)
- Service Layer (logique métier)
- Repository Layer
- Database SQLite (SQLAlchemy)

## Liste des dépendances à installer (PyCharm)

Voici **toutes les dépendances Python** nécessaires pour lancer le projet:

- `PyQt6>=6.7`
- `SQLAlchemy>=2.0`
- `bcrypt>=4.1`
- `PyQt6-Fluent-Widgets>=1.5` (package de `qfluentwidgets`)

## Installation dans PyCharm (recommandé)

1. Ouvrir le dossier `pos-supermarket` dans PyCharm.
2. Configurer l'interpréteur Python (idéalement Python 3.12).
3. Créer/activer un environnement virtuel.
4. Installer les dépendances avec:

```bash
pip install -r requirements.txt
```

## Commandes de démarrage (terminal intégré PyCharm)

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

La base est créée automatiquement dans `data/pos_database.db`.

## Sécurité

- Hash de mot de passe via `bcrypt`
- Authentification via `services/user_service.py`
- Rôles supportés: admin, supervisor, cashier

## Sauvegarde

Le chemin de sauvegarde est prévu via `core/app_config.py` (`data/backup.db`).
