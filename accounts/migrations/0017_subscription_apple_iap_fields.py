from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_user_apple_sub'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='payment_provider',
            field=models.CharField(
                choices=[('stripe', 'Stripe (Web)'), ('apple', 'Apple In-App Purchase (iOS)')],
                default='stripe',
                help_text='Which payment system owns this subscription: Stripe (web) or Apple IAP (iOS)',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='subscription',
            name='apple_original_transaction_id',
            field=models.CharField(
                blank=True,
                help_text='Apple originalTransactionId — stable ID for the IAP subscription across renewals',
                max_length=255,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name='subscription',
            name='apple_product_id',
            field=models.CharField(
                blank=True,
                help_text='Apple IAP product identifier (e.g. com.mytestdmv.standard)',
                max_length=255,
                null=True,
            ),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['apple_original_transaction_id'], name='acc_sub_apple_otxn_idx'),
        ),
    ]
