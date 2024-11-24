import pika

class RabbitConfig:
    ARTICLE_EXCHANGE = "article_exchange"
    ARTICLE_QUEUE = "article_notification_queue"
    ARTICLE_ROUTING_KEY = "article.published"

    USER_EXCHANGE = "user_exchange"
    USER_QUEUE = "user_registration_queue"
    USER_ROUTING_KEY = "user.registered"

def get_rabbit_connection():
    """Membuat koneksi RabbitMQ."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    return connection
