# Generated by Django 3.2.5 on 2021-11-24 18:46

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import info.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatsNew',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField(default=datetime.date.today)),
                ('heading', models.CharField(max_length=255)),
                ('description', models.TextField(max_length=800, verbose_name='Description (HTML allowed)')),
                ('featured', models.BooleanField(default=False)),
                ('include_in_feed', models.BooleanField(default=True)),
                ('notify_users', models.BooleanField(default=True, verbose_name='Notify users (only on new items)')),
                ('emails_sent_count', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='whats_new_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='whats_new_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='ReleaseNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('release_number', models.PositiveIntegerField(default=info.models.incrementReleaseNum, unique=True)),
                ('date', models.DateField(default=datetime.date.today)),
                ('notes', models.TextField(max_length=1000)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='release_note_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='release_note_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-release_number'],
            },
        ),
        migrations.CreateModel(
            name='FaqCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=64, unique=True)),
                ('slug', models.SlugField(editable=False, max_length=100)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='faq_category_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='faq_category_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'FAQ categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Faq',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('question', models.CharField(max_length=255, unique=True)),
                ('answer', models.TextField(verbose_name='Answer (HTML allowed)')),
                ('categories', models.ManyToManyField(related_name='faq_categories', to='info.FaqCategory')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='faq_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='faq_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'FAQ',
                'ordering': ['question'],
            },
        ),
    ]