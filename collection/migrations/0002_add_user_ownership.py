from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_existing_data_to_user(apps, schema_editor):

    User = apps.get_model(
        'auth',
        'User'
    )

    Category = apps.get_model(
        'collection',
        'Category'
    )

    Dress = apps.get_model(
        'collection',
        'Dress'
    )

    # Find the first superuser
    user = (
        User.objects
        .filter(is_superuser=True)
        .order_by('id')
        .first()
    )

    # If no superuser exists, use the first user
    if user is None:

        user = (
            User.objects
            .order_by('id')
            .first()
        )

    if user is None:
        return

    # Assign existing categories
    Category.objects.filter(
        user__isnull=True
    ).update(
        user=user
    )

    # Assign existing dresses
    Dress.objects.filter(
        user__isnull=True
    ).update(
        user=user
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(
            settings.AUTH_USER_MODEL
        ),

        (
            'collection',
            '0001_initial'
        ),
    ]

    operations = [

        # =================================================
        # TEMPORARILY ADD USER TO CATEGORY
        # =================================================

        migrations.AddField(
            model_name='category',
            name='user',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='dress_categories',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # =================================================
        # TEMPORARILY ADD USER TO DRESS
        # =================================================

        migrations.AddField(
            model_name='dress',
            name='user',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='dresses',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # =================================================
        # ASSIGN EXISTING DATA TO CURRENT USER
        # =================================================

        migrations.RunPython(
            assign_existing_data_to_user,
            migrations.RunPython.noop
        ),

        # =================================================
        # MAKE CATEGORY USER REQUIRED
        # =================================================

        migrations.AlterField(
            model_name='category',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='dress_categories',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # =================================================
        # MAKE DRESS USER REQUIRED
        # =================================================

        migrations.AlterField(
            model_name='dress',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='dresses',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]