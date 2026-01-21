from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0028_add_translation_fields_to_questions_and_answers'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='answeroption',
            name='unique_answer_order_per_question',
        ),
    ]
