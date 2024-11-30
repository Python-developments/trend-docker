# Generated by Django 4.2.16 on 2024-11-30 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_alter_customuser_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='bio',
            field=models.TextField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='first_name',
            field=models.CharField(blank=True, max_length=35, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='last_name',
            field=models.CharField(blank=True, max_length=35, null=True),
        ),
    ]
