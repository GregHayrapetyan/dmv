from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0027_add_multilingual_fields_to_lesson_and_category'),
    ]

    operations = [
        # Question translation fields
        migrations.AddField(
            model_name='question',
            name='text_ru',
            field=models.TextField(blank=True, verbose_name='Text (Russian)'),
        ),
        migrations.AddField(
            model_name='question',
            name='explanation_ru',
            field=models.TextField(blank=True, verbose_name='Explanation (Russian)'),
        ),
        migrations.AddField(
            model_name='question',
            name='text_hy',
            field=models.TextField(blank=True, verbose_name='Text (Armenian)'),
        ),
        migrations.AddField(
            model_name='question',
            name='explanation_hy',
            field=models.TextField(blank=True, verbose_name='Explanation (Armenian)'),
        ),
        migrations.AddField(
            model_name='question',
            name='text_hi',
            field=models.TextField(blank=True, verbose_name='Text (Hindi)'),
        ),
        migrations.AddField(
            model_name='question',
            name='explanation_hi',
            field=models.TextField(blank=True, verbose_name='Explanation (Hindi)'),
        ),
        migrations.AddField(
            model_name='question',
            name='text_es',
            field=models.TextField(blank=True, verbose_name='Text (Spanish)'),
        ),
        migrations.AddField(
            model_name='question',
            name='explanation_es',
            field=models.TextField(blank=True, verbose_name='Explanation (Spanish)'),
        ),
        migrations.AddField(
            model_name='question',
            name='text_zh',
            field=models.TextField(blank=True, verbose_name='Text (Chinese)'),
        ),
        migrations.AddField(
            model_name='question',
            name='explanation_zh',
            field=models.TextField(blank=True, verbose_name='Explanation (Chinese)'),
        ),
        # AnswerOption translation fields
        migrations.AddField(
            model_name='answeroption',
            name='text_ru',
            field=models.TextField(blank=True, verbose_name='Text (Russian)'),
        ),
        migrations.AddField(
            model_name='answeroption',
            name='text_hy',
            field=models.TextField(blank=True, verbose_name='Text (Armenian)'),
        ),
        migrations.AddField(
            model_name='answeroption',
            name='text_hi',
            field=models.TextField(blank=True, verbose_name='Text (Hindi)'),
        ),
        migrations.AddField(
            model_name='answeroption',
            name='text_es',
            field=models.TextField(blank=True, verbose_name='Text (Spanish)'),
        ),
        migrations.AddField(
            model_name='answeroption',
            name='text_zh',
            field=models.TextField(blank=True, verbose_name='Text (Chinese)'),
        ),
    ]
