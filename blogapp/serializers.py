from rest_framework import serializers
from .models import Post, Category, Tag
import logging

logger = logging.getLogger(__name__)

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()  # Untuk menampilkan nama atau informasi user
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())  # Menggunakan ID
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)  # Menggunakan ID
    print(category)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'created_at', 'updated_at', 'category', 'tags', 'author', 'is_published']
    
    def validate_title(self, value):
        print(f"title:",{value})
        """
        Validasi untuk memastikan bahwa title post belum ada di database.
        """
        # Jika instance ada, berarti ini adalah update, jadi skip validasi
        if self.instance:
            return value
        
        if Post.objects.filter(title=value).exists():
            raise serializers.ValidationError("A post with this title already exists.")
        return value
