from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient
from .models import User

class RegisterSerializerTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_register_user_success(self):
        data = {
            'username': 'testuser',
            'password': 'securepassword123',
            'password2': 'securepassword123',
        }
        
        response = self.client.post('/api/register/', data, format='json')
        

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('player', response.data)
        self.assertIn('tokens', response.data)

    def test_register_user_password_mismatch(self):
        data = {
            'username': 'testuser',
            'password': 'securepassword123',
            'password2': 'differentpassword123',
        }
        
        response = self.client.post('/api/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], "Les mots de passe ne correspondent pas.")

    def test_register_user_duplicate_username(self):
        User.objects.create_user(username='testuser', password='securepassword123')

        data = {
            'username': 'testuser',
            'password': 'securepassword123',
            'password2': 'securepassword123',
        }
        
        response = self.client.post('/api/register/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0], "Ce nom d'utilisateur est déjà pris.")

