from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import CustomUser, Address

class AccountsAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='Password123!',
            first_name='Test',
            last_name='User'
        )

    def test_user_registration(self):
        data = {
            'email': 'newuser@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
            'first_name': 'New',
            'last_name': 'Customer',
            'phone_number': '9876543210'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data)
        self.assertTrue(CustomUser.objects.filter(email='newuser@example.com').exists())

    def test_user_registration_mismatched_password(self):
        data = {
            'email': 'mismatch@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'DifferentPassword123!',
            'first_name': 'Mismatch',
            'last_name': 'Customer'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        data = {'email': 'test@example.com', 'password': 'Password123!'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')

    def test_user_login_invalid_credentials(self):
        data = {'email': 'test@example.com', 'password': 'WrongPassword'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_address_management_and_isolation(self):
        # User 1 adds address
        self.client.force_authenticate(user=self.user)
        addr_data = {
            'full_name': 'Test User',
            'phone_number': '9876543210',
            'street_address': '123 Fashion Street',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'postal_code': '400001',
            'country': 'India',
            'is_default': True
        }
        res = self.client.post('/api/addresses/', addr_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        addr_id = res.data['id']

        # User 2 cannot access or delete User 1 address
        other_user = CustomUser.objects.create_user(email='other@example.com', password='Password123!')
        self.client.force_authenticate(user=other_user)
        res_other = self.client.get(f'/api/addresses/{addr_id}/')
        self.assertEqual(res_other.status_code, status.HTTP_404_NOT_FOUND)
