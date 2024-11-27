from django_filters.rest_framework import filters, FilterSet

from recipes.models import Tag, Recipe


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(), field_name='tags__slug',
        to_field_name='slug')

    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart')
    is_favorited = filters.BooleanFilter(method='get_is_favorited')

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset

    def get_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ['tags', 'is_in_shopping_cart', 'is_favorited']
