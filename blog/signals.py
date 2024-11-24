from django.db.models.signals import post_save
from django.dispatch import receiver
from blogapp.models import Post
from .rabbitmq.rabbit_utils import publish_message
from .rabbitmq.rabbit_config import RabbitConfig
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def notify_user_registered(sender, instance, created, **kwargs):
    if created:
        message = {
            "username": instance.username,
            "email": instance.email
        }
        publish_message(
            RabbitConfig.USER_EXCHANGE,
            RabbitConfig.USER_ROUTING_KEY,
            message
        )
    
@receiver(post_save, sender=Post)
def notify_article_published(sender, instance, created, **kwargs):
    if created and instance.is_published:
        message = {
            'id': instance.id,
            'title': instance.title,
            'author_id': instance.author.id,
            'created_at': instance.created_at.isoformat()
        }
        # Logic untuk mengirim notifikasi ke RabbitMQ
        print(f"Notifikasi dikirim: {message}")
        publish_message(
            RabbitConfig.ARTICLE_EXCHANGE,
            RabbitConfig.ARTICLE_ROUTING_KEY,
            message
        )
