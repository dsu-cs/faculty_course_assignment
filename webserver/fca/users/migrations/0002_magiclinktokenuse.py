from django.db import migrations
from django.db import models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MagicLinkTokenUse",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("jti", models.CharField(max_length=64, unique=True)),
                ("email", models.EmailField(max_length=254)),
                ("consumed_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
