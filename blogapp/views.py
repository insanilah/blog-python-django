from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from .models import Post, Category, Tag, ExternalPost
from .serializers import PostSerializer, CategorySerializer, TagSerializer
from rest_framework.permissions import IsAuthenticated
from utils.response import api_response
import logging
import requests
from threading import Thread
from .utils.redis_helper import save_to_redis, get_from_redis  # Impor fungsi untuk Redis
from .utils.mongo_helper import save_to_mongo, get_default_collection  # Impor fungsi untuk MongoDB
from .helper import save_user_activity_to_databases  # Impor fungsi untuk MongoDB
from datetime import datetime
from django.db import transaction
from blog.signals import notify_article_published, notify_user_registered

logger = logging.getLogger(__name__)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Set the current user as the author
        serializer.save(author=self.request.user)
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # ada insert ke tabel post dan tabel user activity postgresql
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            # Simpan log aktivitas ke PostgreSQL dan MongoDB
            Thread(target=save_user_activity_to_databases, args=(
                request.user.id, 
                request.user.username, 
                serializer.instance.id
            )).start()

            # Kirim notifikasi ke RabbitMQ setelah artikel berhasil dibuat
            # Thread(target=notify_article_published, args=(serializer.instance,)).start()
        return api_response(
            code=status.HTTP_201_CREATED,
            message="Post created successfully",
            data=serializer.data
        )
        
    def retrieve(self, request, *args, **kwargs):
        # Ambil id dari URL parameter
        pk = kwargs.get('pk')

        # Cek apakah data sudah ada di Redis
        cached_post = get_from_redis(pk)
        
        if cached_post:
            # Jika ada di Redis, langsung return data dari Redis
            # Simpan aktivitas user ke MongoDB secara asinkron hanya sekali
            self.save_user_activity_to_mongo(request.user.id, request.user.username, pk)
            
            return api_response({
                'status': 'success',
                'data': cached_post
            }, status=status.HTTP_200_OK)

        # Jika tidak ada di Redis, ambil dari database
        instance = self.get_object()

        # Serialisasi instance
        serializer = self.get_serializer(instance)

        # Simpan data post ke Redis secara asinkron
        Thread(target=save_to_redis, args=(instance.id, instance)).start()

        # Simpan aktivitas user ke MongoDB secara asinkron
        self.save_user_activity_to_mongo(request.user.id, instance.id)

        # Kembalikan response dengan status 200 OK dan data post
        return api_response(
                code=status.HTTP_200_OK,
                message="Post retrieved successfully",
                data=serializer.data
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return api_response(
            code=status.HTTP_200_OK,
            message="Post updated successfully",
            data=serializer.data
        )
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(
                api_response(
                    code=status.HTTP_200_OK,
                    message="Posts retrieved successfully",
                    data=serializer.data
                ).data
            )

        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            code=status.HTTP_200_OK,
            message="Posts retrieved successfully",
            data=serializer.data
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return api_response(
            code=status.HTTP_204_NO_CONTENT,
            message="Post deleted successfully",
            data=None
        )

    @action(detail=False, methods=['get'])
    def published(self, request):
        published_posts = self.get_queryset().filter(is_published=True)
        serializer = self.get_serializer(published_posts, many=True)
        return api_response(
            code=status.HTTP_200_OK,
            message="Published posts retrieved successfully",
            data=serializer.data
        )
    
    def save_user_activity_to_mongo(self, user_id, username, post_id):
        # Fungsi untuk menyimpan aktivitas user ke MongoDB
        user_activity = {
            "user_id": user_id,
            "username": username,
            "post_id": post_id,
            "activity_type": "viewed",
            "timestamp":datetime.now()
        }
        Thread(target=save_to_mongo, args=(user_id, user_activity)).start()
     
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
def fetch_posts(request):
    try:
        # Mengambil data dari API eksternal
        response = requests.get('https://jsonplaceholder.typicode.com/posts')

        # Mengecek apakah respons berhasil
        if response.status_code == 200:
            data = response.json()  # Mengambil data JSON dari API eksternal
            return api_response(
                code=status.HTTP_200_OK,
                message="Get post external API successfully",
                data=data
            )
        else:
            return api_response(
                code=response.status_code,
                message="Failed to fetch data from external API",
                data=[],
                error=response.text
            )

    except requests.exceptions.RequestException as e:
        # Menangani kesalahan saat melakukan permintaan
        return api_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            data=[],
            error=str(e)
        )

@api_view(['GET'])
def fetch_and_save_external_posts(request):
    try:
        # Ambil data dari API eksternal
        response = requests.get('https://jsonplaceholder.typicode.com/posts')

        # Periksa apakah request berhasil
        if response.status_code == 200:
            posts_data = response.json()

            # Menyimpan data ke dalam database
            saved_posts = []
            for post_data in posts_data:
                # Cek jika post_id sudah ada, jika belum simpan ke database
                external_post, created = ExternalPost.objects.get_or_create(
                    post_id=post_data['id'],  # Gunakan 'id' dari API eksternal sebagai 'post_id'
                    defaults={
                        'user_id': post_data['userId'],
                        'title': post_data['title'],
                        'body': post_data['body']
                    }
                )
                if created:
                    saved_posts.append(external_post)

            # Jika data berhasil disimpan
            return api_response(
                code=status.HTTP_201_CREATED,
                message="External posts fetched and saved successfully",
                data=[{
                    'post_id': post['id'],
                    'user_id': post['userId'],
                    'title': post['title'],
                    'body': post['body']
                } for post in posts_data]
            )
        else:
            return api_response(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to fetch external posts",
                data=[],
                error="External API request failed"
            )

    except requests.exceptions.RequestException as e:
        # Tangani error jika request gagal
        return api_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            data=[],
            error=str(e)
        )
        
def get_user_activities_by_username(username):
    """Ambil aktivitas user dari MongoDB berdasarkan username"""
    print("username:",username)
    # Query untuk mendapatkan aktivitas berdasarkan username
    activities = get_default_collection().find({"username": username}, {"_id": 0, "__v": 0})
    # activitiess = list(activities)
    # activities_json = json.dumps(activitiess, default=json_util.default)
    
    # Format timestamp untuk setiap aktivitas
    formatted_activities = [
        {
            'username': activity["username"],
            'activity': activity["activity"],
            'timestamp': activity["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        }
        for activity in activities
    ]
    print("formatted_activities:",formatted_activities)
    return formatted_activities

@api_view(['GET'])
def get_user_activities_view(request, username):
    """View untuk mendapatkan aktivitas user berdasarkan username"""
    
    try:
        activities = get_user_activities_by_username(username)
        return api_response(
            code=status.HTTP_200_OK,
            message="User activities retrieved successfully",
            data=activities
        )
    except Exception as e:
        return api_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e),
            status=500)
        
@api_view(['GET'])
def aggregate_user_activities_sorted_by_day(request, username):
    """View untuk mengembalikan hasil agregasi aktivitas user"""
    try:
        pipeline = [
            {"$match": {"username": username}},
            {"$project": {"day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}, "activityType": 1}},
            {"$group": {"_id": {"day": "$day", "activityType": "$activityType"}, "activityCount": {"$sum": 1}}},
            {"$project": {"day": "$_id.day", "activityType": "$_id.activityType", "activityCount": 1, "_id": 0}},
            {"$sort": {"day": 1}}
        ]

        result = list(get_default_collection().aggregate(pipeline))
        
        print(result)
        return api_response(
            code=status.HTTP_200_OK,
            message="Aggregation retrieved successfully",
            data=result
        )
    except Exception as e:
        return api_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e),
        )