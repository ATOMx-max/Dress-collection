from django.db import models
from django.contrib.auth.models import User

import os
import uuid


# =========================================================
# IMAGE UPLOAD PATH
# =========================================================

def dress_image_upload_path(instance, filename):
    """
    Store each user's dress images in their own folder
    and generate a unique filename.
    """

    # Get the username
    username = instance.user.username

    # Get the original file extension
    extension = os.path.splitext(filename)[1].lower()

    # Generate a unique filename
    unique_filename = f"{uuid.uuid4().hex}{extension}"

    # Example:
    # dresses/souvik/8f3a91c2....jpg
    return f"dresses/{username}/{unique_filename}"


# =========================================================
# CATEGORY
# =========================================================

class Category(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dress_categories'
    )

    name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=['user', 'name']
            ),
        ]

    def __str__(self):
        return self.name


# =========================================================
# DRESS
# =========================================================

class Dress(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dresses'
    )

    name = models.CharField(
        max_length=150
    )

    photo = models.ImageField(
        upload_to=dress_image_upload_path
    )

    description = models.TextField(
        blank=True
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='dresses'
    )

    color = models.CharField(
        max_length=50
    )

    size = models.CharField(
        max_length=20
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        indexes = [

            # Faster dashboard/home sorting
            models.Index(
                fields=['user', '-created_at']
            ),

            # Faster category filtering
            models.Index(
                fields=['user', 'category']
            ),

            # Faster color filtering
            models.Index(
                fields=['user', 'color']
            ),

            # Faster size filtering
            models.Index(
                fields=['user', 'size']
            ),
        ]

    def __str__(self):
        return self.name


# =========================================================
# FAVORITE
# =========================================================

class Favorite(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    dress = models.ForeignKey(
        Dress,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        # Prevent the same user from
        # favoriting the same dress twice
        unique_together = (
            'user',
            'dress'
        )

        # Newest favorites first
        ordering = [
            '-created_at'
        ]

        indexes = [

            # Faster user's favorite list
            models.Index(
                fields=['user', '-created_at']
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.dress.name}"