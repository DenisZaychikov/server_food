from django.contrib import admin
from .models import (Favorite,
                     Ingredient,
                     Recipe,
                     RecipeIngredient,
                     ShoppingCart,
                     Tag)

admin.site.register(RecipeIngredient)
admin.site.register(Tag)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    def get_favorite_count(self, obj):
        return obj.favorite_set.count()

    get_favorite_count.short_description = 'Добавление рецепта в избранное'

    list_display = ('name', 'author', 'get_favorite_count')
    list_filter = ('name', 'author', 'tags')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
