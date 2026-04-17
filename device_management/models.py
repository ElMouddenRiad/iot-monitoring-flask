import json
import logging

from extensions import db


logger = logging.getLogger(__name__)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    mac = db.Column(db.String(120), unique=True, nullable=False)
    location = db.Column(db.String(120))
    status = db.Column(db.String(20), default='inactive')
    frequency = db.Column(db.Integer, default=30)

    def to_dict(self):
        location_dict = None
        try:
            if self.location:
                location_dict = json.loads(self.location)
        except (json.JSONDecodeError, TypeError):
            pass

        return {
            'id': self.id,
            'name': self.name,
            'mac': self.mac,
            'location': self.location,
            'location_obj': location_dict,
            'status': self.status,
            'frequency': self.frequency
        }

def init_test_devices(app):
    with app.app_context():
        # Check if we already have devices
        if Device.query.count() == 0:
            test_devices = [
                Device(
                    name='San Francisco Sensor',
                    mac='00:00:00:00:00:01',
                    location='{\"latitude\": 37.7749, \"longitude\": -122.4194}',
                    status='active',
                    frequency=30
                ),
                Device(
                    name='New York Sensor',
                    mac='00:00:00:00:00:02',
                    location='{\"latitude\": 40.7128, \"longitude\": -74.0060}',
                    status='active',
                    frequency=30
                )
            ]
            
            for device in test_devices:
                db.session.add(device)
            
            try:
                db.session.commit()
                logger.info("Test devices initialized successfully")
            except Exception as e:
                db.session.rollback()
                logger.exception("Error initializing test devices: %s", e)