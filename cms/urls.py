from django.urls import path
from cms.views import import_questions_view, reorder_tests_view, reorder_lessons_view

app_name = 'cms'

urlpatterns = [
    path('import-questions/', import_questions_view, name='import_questions'),
    path('reorder-tests/', reorder_tests_view, name='reorder_tests'),
    path('reorder-lessons/', reorder_lessons_view, name='reorder_lessons'),
]
