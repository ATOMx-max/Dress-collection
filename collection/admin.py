from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Dress


# =========================================================
# CATEGORY ADMIN
# =========================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'name',
        'description',
    )

    list_filter = (
        'user',
    )

    search_fields = (
        'name',
        'user__username',
    )

    ordering = (
        'name',
    )

    list_per_page = 15


# =========================================================
# DRESS ADMIN
# =========================================================

@admin.register(Dress)
class DressAdmin(admin.ModelAdmin):

    list_display = (
        'photo_preview',
        'user',
        'name',
        'category',
        'color',
        'size',
        'created_at',
    )

    list_filter = (
        'user',
        'category',
        'color',
        'size',
    )

    search_fields = (
        'name',
        'color',
        'size',
        'description',
        'user__username',
    )

    ordering = (
        '-created_at',
    )

    list_per_page = 12

    readonly_fields = (
        'photo_preview',
    )

    fieldsets = (
        (
            '👤 User',
            {
                'fields': (
                    'user',
                )
            }
        ),

        (
            '👗 Dress Information',
            {
                'fields': (
                    'name',
                    'category',
                    'color',
                    'size',
                )
            }
        ),

        (
            '📝 Description',
            {
                'fields': (
                    'description',
                )
            }
        ),

        (
            '📸 Dress Photo',
            {
                'fields': (
                    'photo',
                    'photo_preview',
                )
            }
        ),
    )

    def photo_preview(self, obj):

        if obj.photo:
            return format_html(
                '''
                <div style="
                    width:90px;
                    height:115px;
                    border-radius:12px;
                    overflow:hidden;
                    background:#f3f4f6;
                    border:1px solid #e5e7eb;
                    box-shadow:0 3px 10px rgba(0,0,0,0.08);
                ">
                    <img
                        src="{}"
                        style="
                            width:100%;
                            height:100%;
                            object-fit:cover;
                            display:block;
                        "
                    >
                </div>
                ''',
                obj.photo.url
            )

        return format_html(
            '''
            <div style="
                width:90px;
                height:115px;
                border-radius:12px;
                background:#f3f4f6;
                border:1px dashed #cbd5e1;
                display:flex;
                align-items:center;
                justify-content:center;
                text-align:center;
                color:#64748b;
                font-size:12px;
                font-weight:600;
            ">
                No Image
            </div>
            '''
        )

    photo_preview.short_description = "Photo"