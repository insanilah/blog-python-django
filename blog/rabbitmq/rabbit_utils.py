import pika
import json
from .rabbit_config import RabbitConfig, get_rabbit_connection

def publish_message(exchange, routing_key, message):
    """Mengirim pesan ke RabbitMQ."""
    try:
        connection = get_rabbit_connection()
        channel = connection.channel()

        # Deklarasi exchange
        channel.exchange_declare(exchange=exchange, exchange_type='direct', durable=True)

        # Kirim pesan
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(content_type='application/json')
        )
        connection.close()
    except Exception as e:
        print(f"Failed to publish message: {e}")
