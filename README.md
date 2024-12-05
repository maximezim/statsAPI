# API de Gestion des Interactions

API permettant de gérer et d'analyser les interactions des utilisateurs. Cette API offre des fonctionnalités telles que la création d'utilisateurs, l'authentification, la soumission et la récupération des interactions, ainsi que des statistiques avancées sur l'utilisation et les feedbacks.

## Table des Matières

- [API de Gestion des Interactions](#api-de-gestion-des-interactions)
  - [Table des Matières](#table-des-matières)
  - [Fonctionnalités](#fonctionnalités)
  - [Technologies Utilisées](#technologies-utilisées)
  - [Installation](#installation)
    - [Prérequis](#prérequis)
    - [Configuration avec Docker](#configuration-avec-docker)
  - [Utilisation](#utilisation)
    - [Démarrage de l'Application](#démarrage-de-lapplication)
    - [Documentation Swagger](#documentation-swagger)

## Fonctionnalités

- **Gestion des Utilisateurs** : Création et authentification des utilisateurs avec rôles (admin et utilisateur).
- **Soumission d'Interactions** : Enregistrement des actions des utilisateurs.
- **Récupération des Interactions** : Accès aux interactions globales ou spécifiques à un utilisateur.
- **Statistiques Avancées** : Calcul de statistiques d'utilisation, d'interactions et de feedbacks avec mise en cache.
- **Sécurité Renforcée** : Utilisation de JWT pour l'authentification et des rôles pour l'autorisation.
- **Documentation Interactive** : Interface Swagger pour tester et documenter les endpoints.

## Technologies Utilisées

- **FastAPI** : Framework web performant pour Python.
- **PostgreSQL** : Base de données relationnelle.
- **Redis** : Cache en mémoire pour optimiser les performances.
- **Docker** : Conteneurisation de l'application pour une déploiement simplifié.
- **SQLAlchemy** : ORM pour la gestion de la base de données.
- **JWT (JSON Web Tokens)** : Gestion sécurisée des tokens d'authentification.
- **Swagger** : Documentation interactive des API.

## Installation

### Prérequis

- **Docker** installés sur votre machine.

### Configuration avec Docker

1. **Cloner le Dépôt**

2. **Configuration des Variables d'Environnement**

Créez un fichier `.env` à la racine du projet et ajoutez les variables nécessaires :

```env
ALGORITHM=HS256
```

3. **Construire et Démarrer les Conteneurs**
   
Utilisez Docker Compose pour construire et démarrer les services :

```bash
docker-compose up --build
```

## Utilisation  

### Démarrage de l'Application  

Une fois les conteneurs démarrés, l'application sera accessible à l'adresse suivante :
```
http://localhost
```

### Documentation Swagger

FastAPI intègre une documentation interactive accessible via Swagger. Vous pouvez y accéder en naviguant vers :
```
http://localhost/docs
```

