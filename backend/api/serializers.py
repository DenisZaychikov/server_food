from django.contrib.auth import get_user_model
from django.db.transaction import atomic
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField

from recipes.models import (Favorite,
                            Ingredient,
                            Recipe,
                            RecipeIngredient,
                            ShoppingCart,
                            Tag)
from users.models import Subscription


User = get_user_model()


class CustomUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'last_name',
                  'first_name',
                  'email')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id',
                  'name',
                  'color',
                  'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id',
                  'name',
                  'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = RecipeIngredient
        fields = ('id',
                  'amount',
                  'name',
                  'measurement_unit')


class CreateRecipeIngredientSerializer(serializers.ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    author = CustomUserSerializer()

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'ingredients',
                  'name',
                  'text',
                  'cooking_time',
                  'image',
                  'is_in_shopping_cart',
                  'is_favorited',
                  'author')

    def get_is_in_shopping_cart(self, obj):
        try:
            user = self.context['request'].user
        except KeyError:
            return False
        if user.is_authenticated:
            return ShoppingCart.objects.filter(
                recipe=obj, user=user
            ).exists()
        return False

    def get_is_favorited(self, obj):
        try:
            user = self.context['request'].user
        except KeyError:
            return False
        if user.is_authenticated:
            return Favorite.objects.filter(
                recipe=obj, user=user
            ).exists()
        return False


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateRecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'ingredients',
                  'name',
                  'text',
                  'cooking_time',
                  'image')

    def validate(self, data):
        tags = data['tags']
        ingredients = data['recipe_ingredients']
        if not tags:
            raise ValidationError('Список тэгов пуст.')
        if not ingredients:
            raise ValidationError('Список ингредиентов пуст.')
        if len(tags) != len(set(tags)):
            raise ValidationError('В тэгах есть дубликаты.')
        ingredient_ids = set(
            ingredient['id'].id for ingredient in ingredients
        )
        if len(ingredients) != len(ingredient_ids):
            raise ValidationError('В ингредиентах есть дубликаты.')
        return data

    @atomic()
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @atomic()
    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe.ingredients.clear()
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return super().update(recipe, validated_data)

    @staticmethod
    def create_ingredients(recipe, ingredients):
        for ingredient in ingredients:
            cur_ingredient = Ingredient.objects.get(
                id=ingredient['id'].id)
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=cur_ingredient,
                amount=ingredient['amount']
            )

    def to_representation(self, instance):
        return RecipeSerializer(instance).data


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('username',
                  'last_name',
                  'first_name',
                  'email',
                  'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }


class RecipeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'cooking_time',
                  'image')


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = RecipeInfoSerializer(many=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email',
                  'first_name',
                  'last_name',
                  'username',
                  'id',
                  'is_subscribed',
                  'recipes')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated and Subscription.objects.filter(
                user=user,
                author=obj
                ).exists()
        )
