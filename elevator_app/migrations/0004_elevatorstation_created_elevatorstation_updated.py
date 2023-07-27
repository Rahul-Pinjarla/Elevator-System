# Generated by Django 4.2.3 on 2023-07-27 21:17

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("elevator_app", "0003_alter_elevatorsystem_curr_station"),
    ]

    operations = [
        migrations.AddField(
            model_name="elevatorstation",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="elevatorstation",
            name="updated",
            field=models.DateTimeField(auto_now=True),
        ),
    ]