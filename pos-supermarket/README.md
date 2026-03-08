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

## Compte administrateur par défaut

Au premier démarrage (initialisation DB), le système crée automatiquement un compte admin si absent:

- **Nom d'utilisateur**: `admin`
- **Mot de passe**: `Admin@12345`

Vous pouvez personnaliser ces valeurs via des variables d'environnement avant lancement:

- `POS_DEFAULT_ADMIN_USERNAME`
- `POS_DEFAULT_ADMIN_PASSWORD`
- `POS_DEFAULT_ADMIN_NOM`
- `POS_DEFAULT_ADMIN_PRENOM`
- `POS_DEFAULT_ADMIN_EMPLOYEE_CODE`

## Dashboard Admin (fonctionnel)

Le dashboard admin inclut désormais:

- Menu latéral: Dashboard, Produits, Promotions, Utilisateurs, Stock, Rapports, Paramètres
- Cartes statistiques en temps réel: total produits, produits en rupture/stock min, promotions actives, ventes du jour
- Recherche rapide produit (nom/code-barres) avec tableau de résultats
- Notifications système
- Activité récente (produits/promotions/utilisateurs créés)
- Actions rapides: ajouter produit, créer promotion, créer utilisateur
- Module Produits: suppression produit, activation/désactivation
- Module Stock: renouvellement stock, mise à jour stock exact, alertes rupture
- Formulaire produit complet: nom, code-barres, référence interne, catégorie, marque, prix achat/vente, TVA, stock min/max, unité, expiration, fournisseur, image, éligibilité promotion
- Thème visuel moderne (QSS): boutons arrondis, couleurs pro, tableaux stylisés, menu latéral icônes
- Splash screen animé au démarrage avec message: "Bienvenue sur MOKAT MARKET POS" + "POWERED BY SOCAFTDYINDUSTRUAP"
- Historique des mouvements de stock (entrée/sortie/ajustement/inventaire) avec date, raison et utilisateur

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
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

### Windows (PowerShell) — version fiable

> Dans PowerShell, **n'utilisez pas** `source .venv/bin/activate` (commande Linux).

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## Script automatique Windows (recommandé)

Depuis `pos-supermarket`, lancez:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Ou pour setup + lancement direct:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1 -RunApp
```

Le script:
- vérifie `py`
- crée `.venv`
- installe les dépendances
- vérifie les imports critiques (`sqlalchemy`, `bcrypt`, `PyQt6`)
- peut lancer l'application

## Dépannage Windows (erreurs que vous avez eues)

### 1) `Python est introuvable`

Cause: Python n'est pas installé correctement (ou alias Microsoft Store actif).

Solution:

1. Installer Python 3.12 depuis le site officiel: https://www.python.org/downloads/windows/
2. Pendant l'installation, cocher **"Add python.exe to PATH"**.
3. Désactiver les alias Microsoft Store:
   - `Paramètres > Applications > Paramètres avancés des applications > Alias d'exécution des applications`
   - Désactiver `python.exe` et `python3.exe`.
4. Fermer/réouvrir le terminal puis vérifier:

```powershell
py --version
python --version
```

### 2) `source : Le terme 'source' n'est pas reconnu`

Cause: `source` est une commande Bash/Linux.

Solution PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3) `pip n'est pas reconnu`

Cause: `pip` n'est pas dans PATH ou environnement non activé.

Solution universelle (recommandée):

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4) Erreur d'exécution de scripts PowerShell (`Activate.ps1` bloqué)

Si besoin, autoriser les scripts pour l'utilisateur courant:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Puis rouvrir un terminal et relancer l'activation.

### 5) Avertissement PSReadLine dans PyCharm

Ce n'est pas bloquant pour lancer l'app, mais vous pouvez le corriger avec:

```powershell
Install-Module PSReadLine -MinimumVersion 2.0.3 -Scope CurrentUser -Force
```

La base est créée automatiquement dans `data/pos_database.db`.

## Sécurité

- Hash de mot de passe via `bcrypt`
- Authentification via `services/user_service.py`
- Rôles supportés: admin, supervisor, cashier

## Sauvegarde

Le chemin de sauvegarde est prévu via `core/app_config.py` (`data/backup.db`).
