"""Tests for the ingredients API."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    """Create ingredient url."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

def create_user(email='user@example.com', password='testpass123'):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)

class PublickIngredientApiTests(TestCase):
    """Test unauthenticated API request."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication required for retrieving ingredient."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test auth required for retrieving ingredients."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_igredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name='Ing1')
        Ingredient.objects.create(user=self.user, name='Ing2')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limited_to_user(self):
        """Test list of ingredients limited to authenticated user."""
        new_user =  create_user(email='user2@example.com')
        Ingredient.objects.create(user=new_user, name='Ing1')
        ing = Ingredient.objects.create(user=self.user, name='Ing2')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ing.name)
        self.assertEqual(res.data[0]['id'], ing.id)

    def test_update_ingredient(self):
        """Test updating the ingredients."""
        ing = Ingredient.objects.create(user=self.user, name='Salt')

        payload = {'name': 'Pepper'}
        url = detail_url(ing.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ing.refresh_from_db()
        self.assertEqual(ing.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting ingredient."""
        ing = Ingredient.objects.create(user=self.user, name='Salt')

        url = detail_url(ing.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())


