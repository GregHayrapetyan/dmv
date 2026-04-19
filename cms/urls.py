from django.urls import path
from cms.views import (
    import_questions_view, export_questions_view,
    import_test_questions_view, export_test_questions_view,
    reorder_tests_view, reorder_lessons_view,
)

app_name = 'cms'

urlpatterns = [
    path('import-questions/', import_questions_view, name='import_questions'),
    path('export-questions/', export_questions_view, name='export_questions'),
    path('test/<int:test_id>/import-questions/', import_test_questions_view, name='import_test_questions'),
    path('test/<int:test_id>/export-questions/', export_test_questions_view, name='export_test_questions'),
    path('reorder-tests/', reorder_tests_view, name='reorder_tests'),
    path('reorder-lessons/', reorder_lessons_view, name='reorder_lessons'),
]
