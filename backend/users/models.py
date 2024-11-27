from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        max_length=250,
        unique=True,
    )
    username = models.CharField(
        max_length=250,
        unique=True,
    )
    first_name = models.CharField(
        max_length=250,
    )
    last_name = models.CharField(
        max_length=250
    )
    password = models.CharField(
        max_length=250,
    )
    REQUIRED_FIELDS = ('email', 'first_name', 'last_name')

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='subscriber')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='subscription_author')

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
