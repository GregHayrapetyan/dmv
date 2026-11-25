from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import Subscription
from learning.models import AnswerOption, Lesson, Question, Test, TestAttempt

# Create your tests here.

User = get_user_model()


class PremiumContentAccessTests(TestCase):
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

    def test_anonymous_must_authenticate(self):
        self.assertEqual(self.client.get(self.lesson_url).status_code, 401)
        self.assertEqual(self.client.get(self.test_url).status_code, 401)
        self.assertEqual(self.client.post(self.submit_url, self.answers, format='json').status_code, 401)

    def test_apple_guest_with_subscription_can_open_lesson_and_take_test(self):
        guest = User.objects.create_user(email='guest-1@guest.invalid', is_guest=True)
        Subscription.objects.create(user=guest, payment_provider='apple', status='active')
        self.client.force_authenticate(guest)

        self.assertEqual(self.client.get(self.lesson_url).status_code, 200)
        self.assertEqual(self.client.get(self.test_url).status_code, 200)
        self.assertEqual(self.client.post(self.submit_url, self.answers, format='json').status_code, 200)

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
