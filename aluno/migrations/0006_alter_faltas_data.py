# Generated by Django 5.1.2 on 2024-11-11 19:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aluno", "0005_remove_aluno_faltas_alter_faltas_data_aluno_faltas"),
    ]

    operations = [
        migrations.AlterField(
            model_name="faltas",
            name="data",
            field=models.DateField(default=datetime.date.today, null=True),
        ),
    ]
