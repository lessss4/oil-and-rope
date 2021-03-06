from unittest import mock

from django.contrib.auth import get_user, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.shortcuts import reverse
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _
from faker import Faker
from model_bakery import baker

from registration.views import ActivateAccountView


class TestLoginView(TestCase):
    """
    Checks LoginView works correctly.
    """

    def setUp(self):
        self.faker = Faker()
        self.user = baker.make(get_user_model())
        self.url = reverse('registration:login')

    def test_access_ok(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, 'User cannot access view.')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_user_can_login_ok(self):
        # Change password so we can control input
        password = ''.join(self.faker.words(4))
        self.user.set_password(password)
        self.user.save()
        data = {
            'username': self.user.username,
            'password': password
        }

        self.assertFalse(get_user(self.client).is_authenticated, 'User is logged before post to Login.')
        self.client.post(self.url, data=data)
        self.assertTrue(get_user(self.client).is_authenticated, 'User is not logged.')

    @mock.patch('registration.views.messages')
    def test_user_inactive_warning_ko(self, mock_call: mock.MagicMock):
        # Change password so we can control input
        password = ''.join(self.faker.words(4))
        self.user.set_password(password)
        # Set user as inactive
        self.user.is_active = False
        self.user.save()
        data = {
            'username': self.user.username,
            'password': password
        }

        self.assertFalse(get_user(self.client).is_authenticated, 'User is logged before post to Login.')
        response = self.client.post(self.url, data=data)
        self.assertFalse(get_user(self.client).is_authenticated, 'Inactive user is logged.')

        warn_message = '{}. {}'.format(
            _('Seems like this user is inactive'),
            _('Have you confirmed your email?')
        )
        mock_call.warning.assert_called_with(
            response.wsgi_request,
            warn_message
        )

    def test_invalid_credentials(self):
        """
        Since we access user on LoginView, invalid credentials should be captured by an Exception to avoid 500.
        """

        data = {
            'username': self.faker.word(),
            'password': self.faker.word()
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200, 'Request gives {status}.'.format(
            status=response.status_code
        ))

    def test_cannot_access_if_user_is_logged(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302, 'User is not redirected.')


class TestSignUpView(TestCase):
    """
    Checks if SignUpview works correctly.
    """

    def setUp(self):
        self.faker = Faker()
        profile = self.faker.simple_profile()
        email = self.faker.safe_email()
        password = ''.join(self.faker.words(3))
        self.data_ok = {
            'username': profile['username'],
            'email': email,
            'password1': password,
            'password2': password
        }
        self.url = reverse('registration:register')

    def test_access_ok(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, 'User cannot access view.')
        self.assertTemplateUsed(response, 'registration/register.html')

    @mock.patch('registration.views.messages')
    def test_user_can_register_ok(self, mock_call: mock.MagicMock):
        response = self.client.post(self.url, data=self.data_ok)
        succes_message = '{} {}.'.format(
            _('User created!'),
            _('Please confirm your email')
        )
        mock_call.success.assert_called_with(
            response.wsgi_request,
            succes_message
        )

    def test_user_is_created_ok(self):
        self.client.post(self.url, data=self.data_ok)
        user_exists = get_user_model().objects.filter(username=self.data_ok['username']).exists()
        self.assertTrue(user_exists, 'User is not created.')

    def test_email_sent_ok(self):
        with self.settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            self.client.post(self.url, data=self.data_ok, follow=True)
            self.assertTrue(len(mail.outbox) == 1, 'Email wasn\'t sent.')

    def test_wrong_confim_password(self):
        data_ko = self.data_ok.copy()
        data_ko['password2'] = self.faker.word()
        response = self.client.post(self.url, data=data_ko)
        self.assertFormError(response, 'form', 'password2', 'The two password fields didn\'t match.')

    def test_required_fields_not_given(self):
        data_without_email = self.data_ok.copy()
        del data_without_email['email']
        response = self.client.post(self.url, data=data_without_email)
        self.assertFormError(response, 'form', 'email', 'This field is required.')

        data_without_username = self.data_ok.copy()
        del data_without_username['username']
        response = self.client.post(self.url, data=data_without_username)
        self.assertFormError(response, 'form', 'username', 'This field is required.')

        data_without_password1 = self.data_ok.copy()
        del data_without_password1['password1']
        response = self.client.post(self.url, data=data_without_password1)
        self.assertFormError(response, 'form', 'password1', 'This field is required.')

        data_without_password2 = self.data_ok.copy()
        del data_without_password2['password2']
        response = self.client.post(self.url, data=data_without_password2)
        self.assertFormError(response, 'form', 'password2', 'This field is required.')

    def test_cannot_access_if_user_is_logged(self):
        user = baker.make(get_user_model())
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302, 'User is not redirected.')


class TestActivateAccountView(TestCase):
    """
    Checks correct behaviour for ActivateAccountView.

    We don't validate `access_ok` since a 200 code is not expected from this view.
    """

    def setUp(self):
        self.faker = Faker()
        token_generator = PasswordResetTokenGenerator()
        self.user = baker.make(get_user_model())
        self.user.is_active = False
        self.user.save()
        self.token = token_generator.make_token(self.user)

    @mock.patch('registration.views.messages')
    def test_validates_ok(self, mock_call: mock.MagicMock):
        url = reverse('registration:activate', kwargs={
            'token': self.token,
            'pk': self.user.pk
        })
        response = self.client.get(url)
        self.assertRedirects(response, ActivateAccountView.url)
        mock_call.success.assert_called_with(
            response.wsgi_request,
            _('Your email has been confirmed!')
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active, 'User is not active.')
