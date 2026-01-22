from django.urls import path
from cms.views import import_questions_view

app_name = 'cms'

urlpatterns = [
    path('import-questions/', import_questions_view, name='import_questions'),
]
