from django.conf import settings
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("preferences", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="facultycoursepreference",
            old_name="crn",
            new_name="course_key",
        ),
        migrations.AlterField(
            model_name="facultycoursepreference",
            name="preference",
            field=models.CharField(
                choices=[("H", "H"), ("X", "X"), ("0", "0"), ("1", "1"), ("2", "2"), ("3", "3")],
                max_length=1,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="facultycoursepreference",
            unique_together={("submission", "course_key")},
        ),
    ]