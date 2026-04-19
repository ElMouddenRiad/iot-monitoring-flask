import os
import threading
from datetime import datetime

from bson import ObjectId
from flask import Flask, jsonify
from flask.json.provider import JSONProvider
from pymongo import MongoClient

from config import configure_app
from extensions import init_socketio, socketio
from monitoring.monitor import start_rabbitmq_consumer


class CustomJSONProvider(JSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _build_mongo_collections():
    mongo_client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/iot_platform"))
    mongo_db = mongo_client[os.getenv("MONGODB_DATABASE", "iot_platform")]
    return mongo_db["temperature_readings"], mongo_db["end_device_metrics"]


def create_app():
    app = Flask(__name__)
    app.json_provider_class = CustomJSONProvider
    configure_app(app)
    init_socketio(app)

    readings_collection, end_device_collection = _build_mongo_collections()

    @app.route("/health")
    def health_check():
        return jsonify({"service": "monitoring", "status": "healthy"}), 200

    @app.route("/api/monitoring/readings/recent", methods=["GET"])
    def get_recent_readings():
        readings = list(readings_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(100))
        return jsonify(readings), 200

    @app.route("/api/monitoring/end-devices/metrics/recent", methods=["GET"])
    def get_recent_end_device_metrics():
        metrics = list(end_device_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(100))
        return jsonify(metrics), 200

    if os.getenv("ENABLE_RABBITMQ_CONSUMER", "true").lower() in {"1", "true", "yes", "on"}:
        thread = threading.Thread(target=start_rabbitmq_consumer, daemon=True)
        thread.start()

    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(app.config.get("PORT", 5003)),
        debug=bool(app.config.get("FLASK_DEBUG", False)),
        use_reloader=False,
    )
