from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from allauth.socialaccount.tests import create_oauth2_tests
from allauth.account import app_settings as account_settings
from allauth.account.models import EmailConfirmation, EmailAddress
from allauth.socialaccount.providers import registry
from allauth.socialaccount.models import SocialAccount
from allauth.tests import MockedResponse
from allauth.utils import get_user_model, email_address_exists

from provider import GoogleProvider

User = get_user_model()

class GoogleTests(create_oauth2_tests(registry.by_id(GoogleProvider.id))):

    def get_mocked_response(self, verified_email=True):
        return MockedResponse(200, """
{"family_name": "Penners", "name": "Raymond Penners",
               "picture": "https://lh5.googleusercontent.com/-GOFYGBVOdBQ/AAAAAAAAAAI/AAAAAAAAAGM/WzRfPkv4xbo/photo.jpg",
               "locale": "nl", "gender": "male",
               "email": "raymond.penners@gmail.com",
               "link": "https://plus.google.com/108204268033311374519",
               "given_name": "Raymond", "id": "108204268033311374519",
                "verified_email": %s }
""" % (repr(verified_email).lower()))

    @override_settings(SOCIALACCOUNT_AUTO_SIGNUP=True,
                       ACCOUNT_SIGNUP_FORM_CLASS=None,
                       ACCOUNT_EMAIL_VERIFICATION
                       =account_settings.EmailVerificationMethod.MANDATORY)
    def test_email_verified(self):
        test_email = 'raymond.penners@gmail.com'
        self.login(self.get_mocked_response(verified_email=True))
        EmailAddress.objects \
            .get(email=test_email,
                 verified=True)
        self.assertFalse(EmailConfirmation.objects \
                             .filter(email_address__email=test_email) \
                             .exists())

    @override_settings(SOCIALACCOUNT_AUTO_SIGNUP=True,
                       ACCOUNT_SIGNUP_FORM_CLASS=None,
                       ACCOUNT_EMAIL_VERIFICATION
                       =account_settings.EmailVerificationMethod.MANDATORY)
    def test_email_unverified(self):
        test_email = 'raymond.penners@gmail.com'
        self.login(self.get_mocked_response(verified_email=False))
        email_address = EmailAddress.objects \
            .get(email=test_email)
        self.assertFalse(email_address.verified)
        self.assertTrue(EmailConfirmation.objects \
                            .filter(email_address__email=test_email) \
                            .exists())

    @override_settings(SOCIALACCOUNT_AUTO_SIGNUP=True,
                       ACCOUNT_SIGNUP_FORM_CLASS=None,
                       ACCOUNT_EMAIL_VERIFICATION
                       =account_settings.EmailVerificationMethod.MANDATORY,
                       ACCOUNT_UNIQUE_EMAIL=True,
                       SOCIALACCOUNT_TRUST_GOOGLE_EMAIL=True)
    def test_match_social_login(self):
        test_email = 'raymond.penners@gmail.com'
        uid = "108204268033311374519"
        u = User.objects.create(username='google_user',
                                email=test_email,
                                password='test_password')
        self.login(self.get_mocked_response())
        self.assertTrue(SocialAccount.objects \
                            .filter(user=u,
                                    uid="108204268033311374519",
                                    provider=self.provider.id)
                            .exists())

    @override_settings(SOCIALACCOUNT_AUTO_SIGNUP=True,
                       ACCOUNT_SIGNUP_FORM_CLASS=None,
                       ACCOUNT_EMAIL_VERIFICATION
                       =account_settings.EmailVerificationMethod.MANDATORY,
                       ACCOUNT_UNIQUE_EMAIL=True,
                       SOCIALACCOUNT_TRUST_GOOGLE_EMAIL=False)
    def test_do_not_match_social_login(self):
        test_email = 'raymond.penners@gmail.com'
        uid = "108204268033311374519"
        u = User.objects.create(username='google_user',
                                email=test_email,
                                password='test_password')
        resp = self.login(self.get_mocked_response())
        self.assertRedirects(resp, reverse('socialaccount_signup'))
        self.assertFalse(SocialAccount.objects \
                            .filter(user=u,
                                    uid="108204268033311374519",
                                    provider=self.provider.id)
                            .exists())

    @override_settings(SOCIALACCOUNT_AUTO_SIGNUP=True,
                       ACCOUNT_SIGNUP_FORM_CLASS=None,
                       ACCOUNT_EMAIL_VERIFICATION
                       =account_settings.EmailVerificationMethod.MANDATORY,
                       ACCOUNT_UNIQUE_EMAIL=True,
                       SOCIALACCOUNT_TRUST_GOOGLE_EMAIL=True)
    def test_match_social_login_inconsistent_uid(self):
        test_email = 'raymond.penners@gmail.com'
        uid = "108204268033311374519"
        other_uid = "108204268033311374518"
        u = User.objects.create(username='google_user',
                                email=test_email,
                                password='test_password')
        social_account = SocialAccount.objects.create(provider=self.provider.id,
                                                      user=u,
                                                      uid=other_uid)
        resp = self.login(self.get_mocked_response())
        self.assertRedirects(resp, reverse('socialaccount_signup'))
        self.assertFalse(SocialAccount.objects \
                            .filter(user=u,
                                    uid="108204268033311374519",
                                    provider=self.provider.id)
                            .exists())

    @override_settings(SOCIALACCOUNT_AUTO_SIGNUP=True,
                       ACCOUNT_SIGNUP_FORM_CLASS=None,
                       ACCOUNT_EMAIL_VERIFICATION
                       =account_settings.EmailVerificationMethod.MANDATORY,
                       ACCOUNT_UNIQUE_EMAIL=True,
                       SOCIALACCOUNT_TRUST_GOOGLE_EMAIL=True)
    def test_match_social_login_mulitple_users(self):
        test_email = 'raymond.penners@gmail.com'
        uid = "108204268033311374519"
        u = User.objects.create(username='google_user',
                                email=test_email,
                                password='test_password')

        other_u = User.objects.create(username='other_google_user',
                                email=test_email,
                                password='test_password')
        resp = self.login(self.get_mocked_response())
        self.assertRedirects(resp, reverse('socialaccount_signup'))
        self.assertFalse(SocialAccount.objects \
                            .filter(user=u,
                                    uid="108204268033311374519",
                                    provider=self.provider.id)
                            .exists())
        self.assertFalse(SocialAccount.objects \
                            .filter(user=other_u,
                                    uid="108204268033311374519",
                                    provider=self.provider.id)
                            .exists())

