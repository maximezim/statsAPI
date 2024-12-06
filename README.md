# API de Gestion des Interactions

API permettant de gérer et d'analyser les interactions des utilisateurs. Cette API offre des fonctionnalités telles que la création d'utilisateurs, l'authentification, la soumission et la récupération des interactions, ainsi que des statistiques avancées sur l'utilisation et les feedbacks.

# Calcul de la prochaine action par IA

L'API permet également de prédire la prochaine action d'un utilisateur en fonction de ses actions précédentes. Cette fonctionnalité prédit la prochaine action avec une probabilité associée. Voir la démo plus bas.
(#démo-prédiction-de-la-prochaine-action)

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
- [Description des Endpoints](#description-des-endpoints)
  - [Gestion des Utilisateurs](#gestion-des-utilisateurs)
    - [Créer un Utilisateur](#créer-un-utilisateur)
    - [Authentification](#authentification)
    - [Vérifier un Token](#vérifier-un-token)
  - [Gestion des Interactions](#gestion-des-interactions)
    - [Soumettre une Interaction](#soumettre-une-interaction)
    - [Récupérer Toutes les Interactions](#récupérer-toutes-les-interactions)
    - [Récupérer les Interactions d'un Utilisateur](#récupérer-les-interactions-dun-utilisateur)
  - [Statistiques](#statistiques)
    - [Statistiques d'Utilisation](#statistiques-dutilisation)
    - [Statistiques des Interactions](#statistiques-des-interactions)
    - [Statistiques des Feedbacks](#statistiques-des-feedbacks)
    - [Prédiction de la Prochaine Action](#prédiction-de-la-prochaine-action)

## Fonctionnalités

- **Gestion des Utilisateurs** : Création et authentification des utilisateurs avec rôles (admin et utilisateur).
- **Soumission d'Interactions** : Enregistrement des actions des utilisateurs.
- **Récupération des Interactions** : Accès aux interactions globales ou spécifiques à un utilisateur.
- **Statistiques Avancées** : Calcul de statistiques d'utilisation, d'interactions et de feedbacks avec mise en cache.
- **Sécurité Renforcée** : Utilisation de JWT pour l'authentification et des rôles pour l'autorisation.
- **Documentation Interactive** : Interface Swagger pour tester et documenter les endpoints. (accessible à [http://localhost](http://localhost/docs#/))
- **Calcul de la prochaine action par IA** : Utilisation des chaînes de Markov pour prédire la prochaine action d'un utilisateur.

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

# Description des Endpoints

## Gestion des Utilisateurs

### Créer un Utilisateur  

*Endpoint* : `/create_user`
*Méthode HTTP* : `POST`

```json
{
  "username": "nom_utilisateur",
  "password": "mot_de_passe"
}
```
Erreur : 400 Bad Request si l'utilisateur existe déjà.

### Authentification

*Endpoint* : `/login`
*Méthode HTTP* : `POST`

```json
{
  "username": "nom_utilisateur",
  "password": "mot_de_passe"
}
```

Réponse :
```json
{
  "access_token": "token_jwt",
  "token_type": "bearer"
}
```
Erreur : 400 Bad Request si les identifiants sont invalides.

### Vérifier un Token

*Endpoint* : `/check-token`
*Méthode HTTP* : `POST`

```json
{
  "access_token": "token_jwt"
}
```

Réponse:  
```json
{
  "valid": true,
  "username": "nom_utilisateur"
}
```
ou
```json
{
  "valid": false,
  "username": null
}
```


## Gestion des Interactions

### Soumettre une Interaction

*Endpoint* : `/interactions/submit`
*Méthode HTTP* : `POST`

```json
{
  "action": "action_effectuée"
}
```
Optionnel - En-têtes :
`Authorization: Bearer <token_jwt>`


```json
{
  "action": "action_effectuée"
}
```

Réponse :
```json
{
  "message": "Interaction enregistrée"
}
```

### Récupérer Toutes les Interactions

*Endpoint* : `/interactions`
*Méthode HTTP* : `GET`  

Authorization: Bearer <token_jwt>
    
 ```json
    [
    {
        "id": 1,
        "username": "utilisateur1",
        "action": "action1",
        "timestamp": "2024-12-05T12:34:56"
    },
    ...
    ]
 ```

Erreur :

403 Forbidden si l'utilisateur n'est pas un admin.
401 Unauthorized si le token est invalide ou absent.

![image](https://github.com/user-attachments/assets/64dfc0a8-4946-493a-88bd-50b75125750e)


### Récupérer les Interactions d'un Utilisateur

*Endpoint* : `/interactions/{username}`  
*Méthode HTTP* : `GET`  
Authorization: Bearer <token_jwt>
Réponse :
```json
{
  "id": 1,
  "username": "utilisateur1",
  "action": "action1",
  "timestamp": "2024-12-05T12:34:56"
}
```
Erreur :
403 Forbidden si l'utilisateur n'est pas un admin.  
401 Unauthorized si le token est invalide ou absent.  

## Statistiques

### Statistiques d'Utilisation

*Endpoint* : `/stats/usage`
*Méthode HTTP* : `GET`

En-têtes :
Authorization: Bearer <token_jwt>

Réponse :
Succès (200 OK) :
```json
{
  "usage_stats": {
    "total_interactions": 1000,
    "total_users": 50
  }
}
```

Erreur :
403 Forbidden si l'utilisateur n'est pas un admin.
401 Unauthorized si le token est invalide ou absent.

### Statistiques des Interactions

*Endpoint* : `/stats/interactions`
*Méthode HTTP* : `GET`

En-têtes :
Authorization: Bearer <token_jwt>


Réponse :
Succès (200 OK) :
```json
{
  "interactions_stats": [
    {
      "username": "utilisateur1",
      "interaction_count": 20
    },
    ...
  ]
}
```

Erreur :
403 Forbidden si l'utilisateur n'est pas un admin.
401 Unauthorized si le token est invalide ou absent.

### Statistiques des Feedbacks

*Endpoint* : `/stats/feedback`
*Méthode HTTP* : `GET`

En-têtes :
Authorization: Bearer <token_jwt>

Réponse :
Succès (200 OK) :
```json
{
  "feedback_stats": [
    {
      "username": "utilisateur1",
      "cluster": 0
    },
    ...
  ]
}
```

Erreur :
403 Forbidden si l'utilisateur n'est pas un admin.
401 Unauthorized si le token est invalide ou absent.

### Prédiction de la Prochaine Action

*Endpoint* : `/predict_next_action/{username}`
*Méthode HTTP* : `GET`

En-têtes :
Authorization: Bearer <token_jwt>

Réponse :
Succès (200 OK) :
```json
{
  "username": "utilisateur1",
  "last_action": "action_précédente",
  "predicted_next_action": "action_predite",
  "probability": 0.75
}
```

ou, si aucune donnée de transition n'est disponible :
```json
Copier le code
{
  "message": "Aucune donnée de transition disponible après l'action 'action_précédente' pour l'utilisateur utilisateur1"
}
```

Erreur :
403 Forbidden si l'utilisateur n'est pas un admin.
401 Unauthorized si le token est invalide ou absent.

## Démo Prédiction de la prochaine action:

On a un utilisateur, ici nommé *acheteur*.
On a enregistré son historique d'actions sur le site grâce à l'API.

Premier scénario avec ces actions:
connexion, navigation sur la page d'accueil, recherche de produits, consultation de fiches produits, ajout d'un produit au panier, modification de la quantité dans le panier, passage à la caisse, saisie des informations de livraison, sélection du mode de paiement, confirmation de la commande, déconnexion
![image](https://github.com/user-attachments/assets/5a7f264d-f0d7-4129-b2d2-d3103b0211a1)

Maintenant pour une suite d'actions plus complètes:
connexion, navigation sur la page d'accueil, recherche de produits, consultation de fiches produits, ajout d'un produit au panier, modification de la quantité dans le panier, passage à la caisse, saisie des informations de livraison, sélection du mode de paiement, confirmation de la commande, déconnexion, connexion, recherche de produits, consultation de fiches produits, recherche de produits, consultation de fiches produits, recherche de produits, consultation de fiches produits, recherche de produits, consultation de fiches produits, ajout d'un produit au panier, recherche de produits, consultation de fiches produits

![image](https://github.com/user-attachments/assets/31cea6b9-3431-4380-a2e8-f482310ad51d)

