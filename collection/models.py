from django.db import models
from django.contrib.auth.models import User


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

    def __str__(self):
        return self.name


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
        upload_to='dresses/'
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

    def __str__(self):
        return self.name
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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'dress')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.dress.name}"