# Generated by Django 4.2 on 2024-07-18 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food_diaries', '0012_remove_exercise_unique_user_date_name_exercise_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calorielog',
            name='calorie',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='calorielog',
            name='carbs',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='calorielog',
            name='fats',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='calorielog',
            name='protein',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='exercise',
            name='energy_per_minute',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='meal',
            name='carbs',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='meal',
            name='energy',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='meal',
            name='fats',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='meal',
            name='image_url',
            field=models.TextField(blank=True, max_length=1500, null=True),
        ),
        migrations.AlterField(
            model_name='meal',
            name='protein',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='waterintake',
            name='water_goal',
            field=models.DecimalField(decimal_places=2, default=0.25, max_digits=10),
        ),
    ]
