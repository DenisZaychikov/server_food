from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient

import json
import os


class Command(BaseCommand):
    help = "Load ingredients"

    def handle(self, *args, **options):
        file_path = os.path.join(
            settings.BASE_DIR,
            'data',
            'ingredients.json'
        )
        print('Началась загрузка ингредиентов.')
        with open(file_path) as f:
            ingredients = json.load(f)
        Ingredient.objects.bulk_create([
            Ingredient(
                name=ingredient['name'],
                measurement_unit=ingredient['measurement_unit'])
            for ingredient in ingredients
        ])
        print('Загрузка ингредиентов завершена.')
