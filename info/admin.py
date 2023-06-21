# Run this in console and just paste output here.
#   ./manage.py admin_generator info

from django.contrib import admin

from .models import FaqCategory, Faq, ReleaseNote


@admin.register(FaqCategory)
class FaqCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'name',
        'slug',
    )
    list_filter = ('created_at', 'created_by', 'updated_at', 'updated_by')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}
    date_hierarchy = 'created_at'


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'question',
        'answer',
    )
    list_filter = ('created_at', 'updated_at')
    raw_id_fields = ('categories',)
    date_hierarchy = 'created_at'


@admin.register(ReleaseNote)
class ReleaseNoteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'release_number',
        'date',
        'notes',
    )
    list_filter = (
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'date',
    )
    date_hierarchy = 'created_at'
    
    