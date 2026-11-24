from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.apple_iap_service import AppleIAPService
from accounts.models import Subscription
from accounts.test_apple_iap import TEST_BUNDLE, TEST_PRODUCTS, make_transaction
from learning.models import AnswerOption, Lesson, Question, Test, TestAttempt

# Create your tests here.

User = get_user_model()


@override_settings(APPLE_IAP_PRODUCTS=TEST_PRODUCTS, APPLE_IAP_BUNDLE_ID=TEST_BUNDLE)
class AppleGuestAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        lesson = Lesson.objects.create(title='Road signs', content='A red octagon means stop.')
        test = Test.objects.create(title='Road signs test', passing_percentage=50)
        question = Question.objects.create(test=test, text='What does a red octagon mean?')
        correct = AnswerOption.objects.create(question=question, text='Stop', is_correct=True)
        AnswerOption.objects.create(question=question, text='Yield', order=2)
        self.lesson_url = reverse('lesson-detail', args=[lesson.id])
        self.test_url = reverse('test-detail', args=[test.id])
        self.submit_url = reverse('test-submit', args=[test.id])
        self.answers = {'answers': {str(question.id): correct.id}}

    def _apple_purchase(self, **kwargs):
        return patch.object(AppleIAPService, 'decode_signed_jws', return_value=make_transaction(**kwargs))

    def test_guest_with_active_apple_purchase_can_open_lesson_and_test(self):
        with self._apple_purchase():
            lesson_resp = self.client.get(self.lesson_url, HTTP_X_APPLE_SIGNED_TRANSACTION='signed-jws')
            test_resp = self.client.get(self.test_url, HTTP_X_APPLE_SIGNED_TRANSACTION='signed-jws')

        self.assertEqual(lesson_resp.status_code, 200)
        self.assertEqual(test_resp.status_code, 200)

    def test_guest_with_expired_apple_purchase_is_forbidden(self):
        with self._apple_purchase(expires_in_days=-1):
            resp = self.client.get(self.lesson_url, HTTP_X_APPLE_SIGNED_TRANSACTION='signed-jws')

        self.assertEqual(resp.status_code, 403)

    def test_anonymous_without_apple_purchase_must_authenticate(self):
        self.assertEqual(self.client.get(self.lesson_url).status_code, 401)
        self.assertEqual(self.client.get(self.test_url).status_code, 401)
        self.assertEqual(self.client.post(self.submit_url, self.answers, format='json').status_code, 401)

    def test_guest_submit_is_graded_but_not_saved(self):
        with self._apple_purchase():
            resp = self.client.post(
                self.submit_url, self.answers, format='json', HTTP_X_APPLE_SIGNED_TRANSACTION='signed-jws'
            )

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data['data']['attempt_id'])
        self.assertEqual(resp.data['data']['correct_answers'], 1)
        self.assertTrue(resp.data['data']['passed'])
        self.assertFalse(TestAttempt.objects.exists())

    def test_registered_user_without_subscription_is_forbidden(self):
        user = User.objects.create_user(email='nosub@example.com', password='pw12345678', is_email_verified=True)
        self.client.force_authenticate(user)

        self.assertEqual(self.client.get(self.lesson_url).status_code, 403)

    def test_subscribed_user_submit_is_saved(self):
        user = User.objects.create_user(email='sub@example.com', password='pw12345678', is_email_verified=True)
        Subscription.objects.create(user=user, status='active')
        self.client.force_authenticate(user)

        resp = self.client.post(self.submit_url, self.answers, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['data']['attempt_id'], TestAttempt.objects.get(user=user).id)
