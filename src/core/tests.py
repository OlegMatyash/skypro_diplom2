from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import User


class SignUpTestCase(APITestCase):
    def test_empty_request(self):
        url = reverse('signup')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.json(),
            {
                'username': ['This field is required.'],
                'password': ['This field is required.'],
                'password_repeat': ['This field is required.']
            }
        )

    def test_weak_password(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'test_user',
                'password': '12345678',
                'password_repeat': '12345678'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_already_exists(self):
        User.objects.create(username='test_user', password=make_password('test_password'))
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'test_user',
                'password': 'q1w2e3R$',
                'password_repeat': 'q1w2e3R$'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.json(),
            {'username': ['A user with that username already exists.']}
        )

    def test_invalid_email(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'test_user',
                'email': 'invalid_email',
                'password': 'q1w2e3R$',
                'password_repeat': 'q1w2e3R$',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.json(),
            {'email': ['Enter a valid email address.']}
        )

    def test_password_does_not_match(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'test_user',
                'password': 'q1w2e3R$',
                'password_repeat': '$R3e2w1q',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.json(),
            {'non_field_errors': ['Passwords must match']}
        )

    def test_minimal_required_fields_success(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'test_user',
                'password': 'q1w2e3R$',
                'password_repeat': 'q1w2e3R$',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        new_user = User.objects.last()
        self.assertDictEqual(
            response.json(),
            {'id': new_user.id, 'username': 'test_user', 'first_name': '', 'last_name': '', 'email': ''}
        )
        self.assertNotEqual(new_user.password, 'q1w2e3R$')
        self.assertTrue(new_user.check_password('q1w2e3R$'))

    def test_all_fields_success(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'test_user',
                'email': 'test@test.com',
                'first_name': 'test_first_name',
                'last_name': 'test_last_name',
                'password': 'q1w2e3R$',
                'password_repeat': 'q1w2e3R$',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        new_user = User.objects.last()
        self.assertDictEqual(
            response.json(),
            {
                'id': new_user.id,
                'username': 'test_user',
                'first_name': 'test_first_name',
                'last_name': 'test_last_name',
                'email': 'test@test.com'
            }
        )
        self.assertNotEqual(new_user.password, 'q1w2e3R$')
        self.assertTrue(new_user.check_password('q1w2e3R$'))


class LoginTestCase(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='test_user',
            password='test_password',
            email='test@test.com'
        )

    def test_invalid_username(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'invalid_username',
                'password': 'test_password'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_password(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'test_user',
                'password': 'invalid_password'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_success(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'test_user',
                'password': 'test_password'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {
            'id': self.user.id,
            'username': 'test_user',
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        })
        self.assertNotEqual(response.cookies['sessionid'].value, '')


class TestProfile(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test_user', password='test_password')

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse('profile'),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.cookies['sessionid'].value, '')

    def test_retrieve_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(),
            {
                'id': self.user.id,
                'username': self.user.username,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'email': self.user.email
            }
        )

    def test_update_user(self):
        self.client.force_login(self.user)
        self.assertEqual(self.user.email, '')
        response = self.client.patch(reverse('profile'), {'email': 'test@test.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(),
            {
                'id': self.user.id,
                'username': self.user.username,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'email': 'test@test.com'
            }
        )
        self.user.refresh_from_db(fields=('email',))
        self.assertEqual(self.user.email, 'test@test.com')


class TestUpdatePassword(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='test_user',
            password='test_password'
        )

    def test_auth_required(self):
        response = self.client.patch(
            reverse('update-password'),
            {
                'old_password': 'test_password',
                'new_password': 'new_password',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_old_password(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse('update-password'),
            {
                'old_password': 'invalid_old_password',
                'new_password': 'new_password',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.json(), {'non_field_errors': ['Вы ввели неверный пароль']})

    def test_success(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse('update-password'),
            {
                'old_password': 'test_password',
                'new_password': 'new_password',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {})
        self.user.refresh_from_db(fields=('password',))
        self.assertTrue(self.user.check_password('new_password'))
