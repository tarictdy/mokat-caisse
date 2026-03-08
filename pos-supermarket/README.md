# POS Supermarket (Offline)

Logiciel de caisse offline en Python avec architecture en couches:

- UI Layer (PyQt6)
- Service Layer (logique métier)
- Repository Layer
- Database SQLite (SQLAlchemy)

## Démarrage

```bash
python -m venv .venv
source .venv/bin/activate
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
