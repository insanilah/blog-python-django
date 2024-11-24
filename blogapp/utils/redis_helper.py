import redis
import json
from django.conf import settings
from blogapp.serializers import PostSerializer

# Setup Redis
redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

def save_to_redis(post_id, post_data):
    """Simpan data post ke Redis"""
     # Serialize post_data (Post object) to dictionary
    serializer = PostSerializer(post_data)
    post_data_dict = serializer.data
    
    # Simpan ke Redis
    redis_client.set(f"post:{post_id}", json.dumps(post_data_dict))

def get_from_redis(post_id):
    """Ambil data post dari Redis"""
    data = redis_client.get(f"post:{post_id}")
    return json.loads(data) if data else None
