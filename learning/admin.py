from django.contrib import admin

from django.contrib import admin
from .models import LessonCategory, Lesson, TestCategory, Test, Question, AnswerOption

admin.site.register(LessonCategory)
admin.site.register(Lesson)
admin.site.register(TestCategory)
admin.site.register(Test)
admin.site.register(Question)
admin.site.register(AnswerOption)

