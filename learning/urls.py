from django.urls import path
from .views import (
    LessonCategoryListView, LessonListView, LessonDetailView,
    TestCategoryListView, TestListView, TestDetailView, TestSubmitView,
    LessonProgressView, UserLessonProgressListView,
    UserTestAttemptsListView, TestAttemptDetailView,
    AddFavoriteLessonView, RemoveFavoriteLessonView, FavoriteLessonsListView
)


urlpatterns = [
    # Lesson endpoints
    path('categories/', LessonCategoryListView.as_view(), name='lesson-categories'),
    path('lessons/', LessonListView.as_view(), name='lessons'),
    path('lessons/<slug:slug>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<int:lesson_id>/progress/', LessonProgressView.as_view(), name='lesson-progress'),
    
    # Test endpoints
    path('test-categories/', TestCategoryListView.as_view(), name='test-categories'),
    path('tests/', TestListView.as_view(), name='tests'),
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
]
