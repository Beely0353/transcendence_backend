# Installation et Configuration du Projet

Ce projet Django nécessite un environnement virtuel pour gérer les dépendances et une base de données PostgreSQL pour le stockage des données. Ce guide explique comment préparer l'environnement, installer les dépendances et configurer la base de données.

## Prérequis

Avant de commencer, assurez-vous d'avoir installé les éléments suivants :

- Python 3.x
- pip (gestionnaire de paquets Python)
- PostgreSQL (ou un autre SGBD compatible si nécessaire)
- Daphne (pour lancer le serveur ASGI)

## Étapes d'installation

### 1. Créer l'environnement virtuel

Tout d'abord, créez un environnement virtuel pour isoler les dépendances du projet.

Sur **Linux/MacOS** :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Sur **Windows** :

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 2. Installer les dépendances

Une fois l'environnement virtuel activé, installez toutes les dépendances en utilisant le fichier requirements.txt fourni dans le projet.

```bash
pip install -r requirements.txt
```

### 3. Créer la base de données

Assurez-vous que vous avez PostgreSQL installé et fonctionnel. Créez une nouvelle base de données pour le projet (par exemple, transcendence) avec les informations suivantes :


```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base de données
CREATE DATABASE transcendence;

# Créer un utilisateur
CREATE USER {USERNAME} WITH PASSWORD '{PASSWORD}';

# Donner les droits à l'utilisateur sur la base de données
GRANT ALL PRIVILEGES ON DATABASE transcendence TO {USERNAME};
```

### 4. Configurer les logs dans les paramètres du projet

Modifiez le fichier settings.py dans le dossier du projet pour vous assurer que la configuration de la base de données et des logs est correcte. La ligne 133 (ou l'endroit approprié dans votre fichier settings.py) devrait contenir les bonnes informations de connexion à la base de données :

```bash
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'transcendence',  # Nom de la base de données
        'USER': '{USERNAME}',        # Utilisateur PostgreSQL
        'PASSWORD': '{PASSWORD}',     # Mot de passe PostgreSQL
        'HOST': 'localhost',      # Hôte de la base de données
        'PORT': '5432',           # Port par défaut de PostgreSQL
    }
}
```

### 5. Appliquer les migrations de la base de données

Avant de démarrer le projet, appliquez les migrations pour créer les tables dans la base de données.

```bash
python manage.py migrate
```
###  6. Lancer le projet avec Daphne

Daphne est un serveur HTTP/ASGI qui permet de gérer les connexions WebSocket et HTTP pour Django.

Pour lancer le projet, utilisez la commande suivante :

```bash
daphne -b 0.0.0.0 -p 8000 transcendence.asgi:application
```
Cela va démarrer le serveur sur l'adresse 0.0.0.0 et le port 8000.
