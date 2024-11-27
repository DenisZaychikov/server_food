from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.permissions import IsAuthor
from api.serializers import (
    CreateRecipeSerializer,
    IngredientSerializer,
    RecipeInfoSerializer,
    RecipeSerializer,
    SubscriptionSerializer,
    TagSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)
from users.models import Subscription

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageNumberPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    ordering = ('-pub_date',)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return CreateRecipeSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return (IsAuthor(),)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['post'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if ShoppingCart.objects.filter(recipe=recipe,
                                       user=request.user).exists():
            return Response(
                {'detail': 'Данное блюдо уже находится в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(recipe=recipe,
                                    user=request.user)
        serializer = RecipeInfoSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if not ShoppingCart.objects.filter(recipe=recipe,
                                           user=request.user).exists():
            return Response(
                {'detail': 'Данное блюдо не находится в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user_recipe = ShoppingCart.objects.get(recipe=recipe,
                                               user=request.user)
        user_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if Favorite.objects.filter(recipe=recipe,
                                   user=request.user).exists():
            return Response(
                {'detail': 'Данное блюдо уже находится в списке любимых блюд'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(recipe=recipe,
                                user=request.user)
        serializer = RecipeInfoSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if not Favorite.objects.filter(recipe=recipe,
                                       user=request.user).exists():
            return Response(
                {'detail': 'Данного блюда нет в списке любимых блюд'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite_dish = Favorite.objects.get(recipe=recipe,
                                             user=request.user)
        favorite_dish.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        recipe_ingredients = RecipeIngredient.objects.values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(
            total_amount=Sum('amount'))
        ingredients_count = {}
        for recipe_ingredient in recipe_ingredients:
            key = f"{recipe_ingredient['ingredient__name']} ({recipe_ingredient['ingredient__measurement_unit']})"
            amount = recipe_ingredient['total_amount']
            ingredients_count[key] = amount
        lines = [f'{key} - {value}' for key, value in
                 ingredients_count.items()]
        response_text = '\n'.join(lines)
        response = HttpResponse(response_text.encode('utf-8'),
                                content_type='text/plain; charset=utf-8')
        return response


class CustomUserViewSet(UserViewSet):
    pagination_class = PageNumberPagination

    @action(methods=['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        recipe_authors = User.objects.filter(
            subscription_author__user=request.user)
        page = self.paginate_queryset(recipe_authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['post'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        recipe_author = get_object_or_404(User, pk=id)
        if recipe_author == request.user:
            return Response(
                {'detail': 'Вы не можете подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(user=request.user,
                                       author=recipe_author).exists():
            return Response(
                {'detail': 'Вы уже подписаны на данного автора'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(user=request.user,
                                    author=recipe_author)
        serializer = SubscriptionSerializer(recipe_author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        recipe_author = get_object_or_404(User, id=id)
        if not Subscription.objects.filter(user=request.user,
                                           author=recipe_author).exists():
            return Response(
                {'detail': 'Вы не подписаны на данного автора'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription = Subscription.objects.get(user=request.user,
                                                author=recipe_author)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
