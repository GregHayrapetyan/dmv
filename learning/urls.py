from django.urls import path
from .views import (
    LessonListView, LessonDetailView,
    TestListView, TestDetailView, TestSubmitView,
    LessonProgressView, UserLessonProgressListView,
    UserTestAttemptsListView, TestAttemptDetailView,
    AddFavoriteLessonView, RemoveFavoriteLessonView, FavoriteLessonsListView,
    TestStatisticsView, CategoryListView, CategoryDetailView,
    DemoTestGenerateView, DemoTestSubmitView
)


urlpatterns = [
    # Category endpoints
    path('categories/', CategoryListView.as_view(), name='categories'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    
    # Lesson endpoints
    path('lessons/', LessonListView.as_view(), name='lessons'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<int:lesson_id>/progress/', LessonProgressView.as_view(), name='lesson-progress'),
    
    # Test endpoints
    path('tests/', TestListView.as_view(), name='tests'),
    path('tests/statistics/', TestStatisticsView.as_view(), name='test-statistics'),
    path('tests/<int:pk>/', TestDetailView.as_view(), name='test-detail'),
    path('tests/<int:pk>/submit/', TestSubmitView.as_view(), name='test-submit'),
    
    # User progress endpoints
    path('my-progress/', UserLessonProgressListView.as_view(), name='my-lesson-progress'),
    path('my-attempts/', UserTestAttemptsListView.as_view(), name='my-test-attempts'),
    path('my-attempts/<int:pk>/', TestAttemptDetailView.as_view(), name='test-attempt-detail'),
    
    # Favorite lessons endpoints
    path('favorites/', FavoriteLessonsListView.as_view(), name='favorite-lessons-list'),
    path('lessons/<int:lesson_id>/favorite/', AddFavoriteLessonView.as_view(), name='add-favorite-lesson'),
    path('lessons/<int:lesson_id>/unfavorite/', RemoveFavoriteLessonView.as_view(), name='remove-favorite-lesson'),
    
    # Demo test endpoints (for non-registered users)
    path('demo-tests/generate/', DemoTestGenerateView.as_view(), name='demo-test-generate'),
    path('demo-tests/<str:test_session_id>/submit/', DemoTestSubmitView.as_view(), name='demo-test-submit'),
]
