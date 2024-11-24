from .models import UserActivity
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def save_user_activity_to_databases(user_id, username, post_id):
    # Simpan ke PostgreSQL
    try:
        UserActivity.objects.create(
            user_id=user_id,
            username=username,
            post_id=post_id,
            activity_type="created",
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Error saving to PostgreSQL: {str(e)}")
