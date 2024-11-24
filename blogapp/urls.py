from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, CategoryViewSet, TagViewSet
from . import views  # Pastikan Anda mengimpor views dari blogapp

router = DefaultRouter()
router.register(r'posts', PostViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('fetch-posts/', views.fetch_posts, name='fetch_posts'),
    path('fetch-and-save-posts/', views.fetch_and_save_external_posts, name='fetch_and_save_external_posts'),
    path('users/user-activities/<str:username>', views.get_user_activities_view, name='get_user_activities_view'),
    path('users/user-activities-summary/<str:username>', views.aggregate_user_activities_sorted_by_day),
]
