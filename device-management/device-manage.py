import pika
import json

def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
        print(f"Received event: {event['event_type']}")
        print(f"Device data: {event['device_data']}")
        print(f"Timestamp: {event['timestamp']}")
        print("-" * 50)
    except Exception as e:
        print(f"Error processing message: {e}")

def main():
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Declare the same queue as in the publisher
    channel.queue_declare(queue='device_events')

    # Set up the consumer
    channel.basic_consume(
        queue='device_events',
        on_message_callback=callback,
        auto_ack=True
    )

    print('Waiting for device events. To exit press CTRL+C')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\nShutting down consumer...")
    finally:
        connection.close()

if __name__ == '__main__':
    main()