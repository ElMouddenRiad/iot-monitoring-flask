# Cloud-IOT-Project

Plateforme IoT cloud pour la gestion d'appareils, le monitoring temps réel et la prédiction de mesures environnementales.

Projet réalisé en 2025.

Le dépôt a été nettoyé pour une présentation plus professionnelle : documentation consolidée dans ce README, configuration externalisée, suppression des artefacts inutiles et réduction des effets de bord au démarrage.

## Vue d'ensemble

L'application combine :

- un backend Flask avec authentification JWT
- une couche de gestion d'appareils IoT
- un flux temps réel via MQTT, RabbitMQ, MongoDB et Socket.IO
- un module de prédiction basé sur scikit-learn
- un dashboard React pour l'administration et la visualisation
- un moniteur pour les appareils de bord / end devices

## Architecture

### Backend
- [app.py](app.py) : point d'entrée principal de l'application Flask
- [config.py](config.py) : configuration centralisée via variables d'environnement
- [extensions.py](extensions.py) : initialisation des extensions partagées
- [signing/auth.py](signing/auth.py) : inscription, connexion, déconnexion et révocation JWT
- [device_management/device_manage.py](device_management/device_manage.py) : routes de gestion des appareils
- [device_management/dal/dal.py](device_management/dal/dal.py) : accès aux données et helpers de lecture
- [device_management/business/device_service.py](device_management/business/device_service.py) : publication et simulation des événements
- [monitoring/monitor.py](monitoring/monitor.py) : stockage et diffusion des mesures
- [mqtt_client.py](mqtt_client.py) : client MQTT côté serveur
- [prediction_module.py](prediction_module.py) : entraînement et prédiction ML
- [wsgi.py](wsgi.py) : entrée de déploiement WSGI pour Gunicorn/uWSGI

### Frontend
- [iot-dashboard](iot-dashboard/) : application React
- [iot-dashboard/src/services/api.js](iot-dashboard/src/services/api.js) : client API configurable
- [iot-dashboard/src/components](iot-dashboard/src/components) : composants UI du tableau de bord

### Services IoT / Edge
- [iot-device/iot.py](iot-device/iot.py) : simulateur d'appareils IoT
- [end-device/end_device.py](end-device/end_device.py) : moniteur d'appareil de bord

## Fonctionnalités

- Authentification JWT avec gestion de révocation
- CRUD des appareils IoT
- Publication et consommation d'événements via RabbitMQ
- Ingestion MQTT et diffusion temps réel vers le dashboard
- Stockage des mesures dans MongoDB
- Prédiction à partir des données Open-Meteo
- Visualisation des appareils, statistiques et graphiques dans React
- Moniteur local pour CPU, mémoire et métriques système

## État du nettoyage technique

Les points suivants ont été corrigés ou réduits :

- suppression des fichiers de documentation secondaires pour garder un seul README
- remplacement des valeurs hardcodées par des variables d'environnement quand c'était possible
- suppression de plusieurs impressions console au profit du logging
- suppression d'effets de bord au chargement dans la DAL
- nettoyage de fichiers morts, doublons et artefacts inutiles
- normalisation des URL côté frontend
- consolidation de l'entrée principale Flask

## Variables d'environnement principales

### Backend
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `JWT_ACCESS_TOKEN_EXPIRES`
- `DATABASE_URL`
- `REDIS_URL`
- `RABBITMQ_URL`
- `RABBITMQ_HOST`
- `RABBITMQ_PORT`
- `RABBITMQ_USERNAME`
- `RABBITMQ_PASSWORD`
- `RABBITMQ_QUEUE`
- `RABBITMQ_EXCHANGE`
- `MQTT_BROKER_URL`
- `MQTT_BROKER_PORT`
- `MQTT_TOPIC`
- `MQTT_CLIENT_ID`
- `ENABLE_MQTT_CLIENT`
- `SKIP_DATABASE_INIT`
- `OPENMETEO_URL`
- `OPEN_METEO_CACHE_DIR`
- `OPEN_METEO_CACHE_TTL`
- `OPEN_METEO_RETRIES`
- `OPEN_METEO_BACKOFF_FACTOR`
- `MONGODB_URI`
- `MONGODB_DATABASE`
- `PORT`
- `FLASK_DEBUG`

### Frontend
- `REACT_APP_API_BASE_URL`

## Installation locale

### 1. Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Le backend est accessible sur `http://localhost:5000`.

### 2. Frontend

```bash
cd iot-dashboard
npm install
npm start
```

Le dashboard est accessible sur `http://localhost:3000`.

### 3. Lancement avec Docker Compose

```bash
docker-compose up --build
```

## Endpoints utiles

### Santé
- `GET /health`

### Authentification
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/protected`

### Appareils
- `GET /api/devices`
- `POST /api/devices`
- `PUT /api/devices/<mac>`
- `DELETE /api/devices/<mac>`
- `GET /api/stats`
- `GET /api/readings/recent`

### Prédiction
- `POST /predict_device`

## Structure du dépôt

```text
Cloud-IOT-Project/
├── app.py
├── config.py
├── extensions.py
├── mqtt_client.py
├── prediction_module.py
├── signing/
├── device_management/
├── monitoring/
├── iot-device/
├── end-device/
├── iot-dashboard/
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
└── wsgi.py
```

## Notes de qualité

- le projet reste orienté démonstration / portfolio, mais la base est maintenant plus propre pour GitHub et pour un CV
- la documentation a été volontairement simplifiée pour éviter la dispersion
- le code est plus cohérent avec une configuration par environnement, ce qui facilite le déploiement et la maintenance

## English summary

Cloud-IOT-Project is a Flask + React IoT platform for device management, real-time monitoring, and environmental prediction.

### What `wsgi.py` is for

`wsgi.py` exposes the Flask application in a production-friendly way. It is used by WSGI servers to start the backend without relying on the development entrypoint in `app.py`.

### Short setup

1. Create the Python virtual environment and install backend dependencies.
2. Start the Flask backend.
3. Install and launch the React dashboard.
4. Optionally deploy with Docker Compose.

### Main strengths

- centralized configuration
- JWT authentication with token revocation
- MQTT, RabbitMQ, MongoDB, and Socket.IO integration
- reusable WSGI deployment entrypoint

## Points à poursuivre si besoin

- modulariser davantage `device_management/device_manage.py`
- durcir la validation des entrées API
- ajouter des tests automatisés
- standardiser encore les logs et les codes d'erreur

## Licence

Aucune licence n'a été ajoutée pour le moment. Ajouter une licence explicite avant publication publique si nécessaire.
