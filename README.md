# Cloud-IOT-Project

Plateforme IoT cloud pour la gestion d'appareils, le monitoring temps reel et la prediction de mesures environnementales.

Projet realise en 2025.

## Vue d'ensemble

L'application combine :

- 3 microservices Flask (`signing`, `device-management`, `monitoring`)
- un broker RabbitMQ pour la communication asynchrone entre services
- MongoDB pour les donnees de monitoring, PostgreSQL pour les donnees relationnelles
- Redis pour la gestion de token/session rapide
- Socket.IO pour les mises a jour temps reel cote client
- un API Gateway NGINX comme point d'entree unique
- des simulateurs IoT (`iot-device`, `end-device`) pour la collecte et l'observabilite

## Architecture

### Microservices
- [microservices/signing/app.py](microservices/signing/app.py) : auth JWT, register/login/logout, health
- [microservices/device-management/app.py](microservices/device-management/app.py) : CRUD devices, stats, end-devices, prediction
- [microservices/monitoring/app.py](microservices/monitoring/app.py) : ingestion RabbitMQ, APIs monitoring, Socket.IO

### Modules metier partages
- [signing/auth.py](signing/auth.py) : logique authentication
- [device_management/device_manage.py](device_management/device_manage.py) : endpoints et persistence des devices
- [device_management/business/device_service.py](device_management/business/device_service.py) : publication d'evenements RabbitMQ
- [monitoring/monitor.py](monitoring/monitor.py) : consumer RabbitMQ + emission Socket.IO
- [prediction_module.py](prediction_module.py) : entrainement/prediction ML
- [config.py](config.py) : configuration centralisee via variables d'environnement
- [extensions.py](extensions.py) : `db` SQLAlchemy et `socketio`

### Frontend
- [iot-dashboard](iot-dashboard/) : application React
- [iot-dashboard/src/services/api.js](iot-dashboard/src/services/api.js) : base URL configurable (`REACT_APP_API_BASE_URL`)

### Services IoT / Edge
- [iot-device/iot.py](iot-device/iot.py) : simulateur IoT MQTT
- [end-device/end_device.py](end-device/end_device.py) : moniteur systeme end-device

### Dossiers complementaires
- [nginx/nginx.conf](nginx/nginx.conf) : routage API Gateway vers les microservices
- [kubernetes](kubernetes/) : manifests de deploiement (base actuelle)

## Communication inter-services

- `signing` <-> clients: HTTP REST via gateway (`/auth/*`)
- `device-management` <-> clients: HTTP REST via gateway (`/api/*`, `/predict_device`)
- `device-management` -> `monitoring`: RabbitMQ (event-driven)
- `monitoring` -> clients: Socket.IO (`/socket.io/`)

## Data flow

- Les devices publient des donnees (MQTT / scripts de simulation).
- `device-management` gere les entites et publie des evenements sur RabbitMQ.
- `monitoring` consomme RabbitMQ, stocke dans MongoDB et pousse en temps reel via Socket.IO.

## Variables d'environnement

### Backend/API
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
- `MQTT_REFRESH_TIME`
- `ENABLE_MQTT_CLIENT`
- `API_MAX_STORED_MESSAGES`
- `API_KEY_REQUIRED`
- `API_SECRET_KEY`
- `SKIP_DATABASE_INIT`
- `OPENMETEO_URL`
- `OPEN_METEO_CACHE_DIR`
- `OPEN_METEO_CACHE_TTL`
- `OPEN_METEO_RETRIES`
- `OPEN_METEO_BACKOFF_FACTOR`
- `MONGODB_URI`
- `MONGODB_DATABASE`
- `DOCKER_ENV`
- `ENABLE_RABBITMQ_CONSUMER`
- `PORT`
- `FLASK_DEBUG`

### End-device script
- `API_URL` (defaut: `http://localhost:5000/api`)

### Frontend
- `REACT_APP_API_BASE_URL` (defaut: `http://localhost:5000`)

## Installation locale

### 1. Backend local (mode developpement)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python microservices/signing/app.py
python microservices/device-management/app.py
python microservices/monitoring/app.py
```

Par defaut:

- Signing: `http://localhost:5001`
- Device management: `http://localhost:5002`
- Monitoring: `http://localhost:5003`

### 2. Frontend

```bash
cd iot-dashboard
npm install
npm start
```

Dashboard disponible sur `http://localhost:3000`.

Configurer `REACT_APP_API_BASE_URL=http://localhost:5000` si vous utilisez le gateway.

### 3. Simulateurs optionnels (hors Docker)

```bash
python iot-device/iot.py
python end-device/end_device.py
```

## Lancement Docker Compose

```bash
docker compose up --build
```

Gateway disponible sur `http://localhost:5000`.

Commande legacy equivalente:

```bash
docker-compose up --build
```

Le fichier `docker-compose.yaml` demarre:

- `signing_service`
- `device_management_service`
- `monitoring_service`
- `nginx_gateway`
- `postgres`, `redis`, `rabbitmq`, `mongodb`, `mqtt`
- `iot_device`, `end_device`

Le frontend React n'est pas lance par ce compose.

## Endpoints API

### Sante
- `GET /health/signing`
- `GET /health/device-management`
- `GET /health/monitoring`

### Authentification
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/protected`

### IoT devices
- `GET /api/devices`
- `POST /api/devices`
- `PUT /api/devices/<mac>`
- `DELETE /api/devices/<mac>`
- `POST /api/devices/start-simulation`
- `GET /api/stats`
- `GET /api/readings/recent`

### End devices
- `POST /api/end-devices/register`
- `GET /api/end-devices`
- `DELETE /api/end-devices/<mac>`
- `POST /api/end-devices/metrics`
- `GET /api/end-devices/metrics/<mac>`

### Prediction
- `POST /predict_device`

### Monitoring APIs
- `GET /api/monitoring/readings/recent`
- `GET /api/monitoring/end-devices/metrics/recent`

## Structure du depot

```text
iot-monitoring-flask/
|- microservices/
|  |- signing/
|  |  |- app.py
|  |  |- Dockerfile
|  |- device-management/
|  |  |- app.py
|  |  |- Dockerfile
|  |- monitoring/
|     |- app.py
|     |- Dockerfile
|- signing/
|- device_management/
|- monitoring/
|- iot-device/
|- end-device/
|- iot-dashboard/
|- nginx/
|  |- nginx.conf
|- kubernetes/
|- docker-compose.yaml
|- requirements.txt
```

## Notes

- Le projet est aligne au modele 3 microservices de l'enonce avec un gateway NGINX.
- Le dossier `kubernetes/` peut etre etendu pour couvrir les 3 microservices explicitement.
- Aucune licence n'a ete ajoutee pour le moment.
