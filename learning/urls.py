from django.urls import path
from .views import (
    LessonCategoryListView, LessonListView, LessonDetailView,
    TestCategoryListView, TestListView, TestDetailView, TestSubmitView
)


urlpatterns = [
    # Lesson endpoints
    path('categories/', LessonCategoryListView.as_view(), name='lesson-categories'),
    path('lessons/', LessonListView.as_view(), name='lessons'),
    path('lessons/<slug:slug>/', LessonDetailView.as_view(), name='lesson-detail'),
    
    # Test endpoints
    path('test-categories/', TestCategoryListView.as_view(), name='test-categories'),
    path('tests/', TestListView.as_view(), name='tests'),
    path('tests/<int:pk>/', TestDetailView.as_view(), name='test-detail'),
    path('tests/<int:pk>/submit/', TestSubmitView.as_view(), name='test-submit'),
]
