from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.utils import timezone
from pathlib import Path
import json
from datetime import timedelta

from .models import Category, Dress, Favorite, DressShare
from .forms import DressForm
from .image_utils import optimize_image

from django.db import transaction
from django.db.models import Q
import logging


logger = logging.getLogger(__name__)


# =========================================================
# DEFAULT CATEGORIES
# =========================================================

def create_default_categories(user):

    default_categories = [
        ('T-Shirts', 'Casual and everyday T-shirts'),
        ('Shirts', 'Casual and formal shirts'),
        ('Jeans', 'Denim and jeans'),
        ('Dresses', 'Dresses and one-piece outfits'),
        ('Sarees', 'Traditional sarees'),
        ('Tops', 'Tops and casual upper wear'),
        ('Jackets', 'Jackets and outerwear'),
        ('Shorts', 'Shorts and casual lower wear'),
        ('Kurtas', 'Traditional and casual kurtas'),
        ('Formal Wear', 'Formal and office wear'),
    ]

    for name, description in default_categories:

        Category.objects.get_or_create(
            user=user,
            name=name,
            defaults={
                'description': description
            }
        )


# =========================================================
# HOME PAGE
# =========================================================

@login_required(login_url='login')
def home(request):

    # Only current user's dresses
    dresses = (
        Dress.objects
        .filter(user=request.user)
        .select_related('category')
    )

    # ==============================
    # SEARCH
    # ==============================

    search_query = request.GET.get('search', '').strip()

    if search_query:
        dresses = dresses.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(color__icontains=search_query) |
            Q(size__icontains=search_query)
        )

    # ==============================
    # CATEGORY FILTER
    # ==============================

    category_filter = request.GET.get('category', '').strip().lower()

    if category_filter and category_filter != 'all':
        dresses = dresses.filter(
            category__name__iexact=category_filter
        )

    # ==============================
    # COLOR FILTER
    # ==============================

    color_filter = request.GET.get('color', '').strip().lower()

    if color_filter and color_filter != 'all':
        dresses = dresses.filter(
            color__iexact=color_filter
        )

    # ==============================
    # SIZE FILTER
    # ==============================

    size_filter = request.GET.get('size', '').strip().lower()

    if size_filter and size_filter != 'all':
        dresses = dresses.filter(
            size__iexact=size_filter
        )

    # ==============================
    # SORTING
    # ==============================

    sort_filter = request.GET.get('sort', 'default').strip()

    if sort_filter == 'name-asc':
        dresses = dresses.order_by('name')

    elif sort_filter == 'name-desc':
        dresses = dresses.order_by('-name')

    elif sort_filter == 'newest':
        dresses = dresses.order_by('-created_at')

    elif sort_filter == 'oldest':
        dresses = dresses.order_by('created_at')

    else:
        # Same default ordering as before
        dresses = dresses.order_by('-created_at')

    # ==============================
    # PAGINATION
    # ==============================

    paginator = Paginator(dresses, 12)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # ==============================
    # CURRENT USER'S CATEGORIES
    # ==============================

    categories = (
        Category.objects
        .filter(user=request.user)
        .order_by('name')
    )

    # ==============================
    # COLORS USED BY CURRENT USER
    # ==============================

    colors = (
        Dress.objects
        .filter(user=request.user)
        .values_list('color', flat=True)
        .distinct()
        .order_by('color')
    )

    # ==============================
    # SIZES USED BY CURRENT USER
    # ==============================

    sizes = (
        Dress.objects
        .filter(user=request.user)
        .values_list('size', flat=True)
        .distinct()
        .order_by('size')
    )

    # ==============================
    # CURRENT USER'S FAVORITES
    # ==============================

    favorite_ids = set(
        Favorite.objects
        .filter(
            user=request.user,
            dress__user=request.user
        )
        .values_list('dress_id', flat=True)
    )

    return render(
        request,
        'collection/home.html',
        {
            'dresses': page_obj,
            'page_obj': page_obj,

            'categories': categories,
            'colors': colors,
            'sizes': sizes,

            'favorite_ids': favorite_ids,

            # Keep filter values
            'search_query': search_query,
            'category_filter': category_filter,
            'color_filter': color_filter,
            'size_filter': size_filter,
            'sort_filter': sort_filter,
        }
    )


# =========================================================
# DRESS DETAIL
# =========================================================

@login_required(login_url='login')
def dress_detail(request, dress_id):

    dress = get_object_or_404(
        Dress.objects.select_related('category'),
        id=dress_id,
        user=request.user
    )

    return render(
        request,
        'collection/dress_detail.html',
        {
            'dress': dress
        }
    )


# =========================================================
# PERSONAL DASHBOARD
# =========================================================

@login_required(login_url='login')
def admin_dashboard(request):

    total_dresses = Dress.objects.filter(
        user=request.user
    ).count()

    total_categories = Category.objects.filter(
        user=request.user
    ).count()

    recent_dresses = (
        Dress.objects
        .filter(user=request.user)
        .select_related('category')
        .order_by('-created_at')[:5]
    )

    return render(
        request,
        'admin/dashboard.html',
        {
            'total_dresses': total_dresses,
            'total_categories': total_categories,
            'recent_dresses': recent_dresses,
        }
    )


# =========================================================
# DRESS LIST
# =========================================================

@login_required(login_url='login')
def dashboard_dresses(request):

    dresses = (
        Dress.objects
        .filter(user=request.user)
        .select_related('category')
        .order_by('-created_at')
    )

    paginator = Paginator(dresses, 12)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'admin/dresses.html',
        {
            'dresses': page_obj,
            'page_obj': page_obj,
        }
    )


# =========================================================
# ADD DRESS
# =========================================================

@login_required(login_url='login')
def add_dress(request):

    if request.method == 'POST':

        form = DressForm(
            request.POST,
            request.FILES,
            user=request.user
        )

        if form.is_valid():

            try:

                dress = form.save(commit=False)

                dress.user = request.user

                # ==========================================
                # OPTIMIZE + CONVERT IMAGE TO JPEG
                # ==========================================

                if 'photo' in request.FILES:

                    optimized_image = optimize_image(
                        request.FILES['photo']
                    )

                    original_name = request.FILES['photo'].name

                    base_name = original_name.rsplit(
                        '.',
                        1
                    )[0]

                    dress.photo.save(
                        f"{base_name}.jpg",
                        optimized_image,
                        save=False
                    )

                dress.save()

                return redirect('dashboard_dresses')

            except Exception as e:

                logger.exception("ADD DRESS ERROR")

                return HttpResponse(
                    f"""
                    <html>
                    <head>
                        <title>Add Dress Error</title>
                    </head>

                    <body style="
                        font-family: Arial, sans-serif;
                        padding: 40px;
                        background: #f8fafc;
                    ">

                        <h2 style="
                            color: #dc2626;
                        ">
                            Add Dress Error
                        </h2>

                        <pre style="
                            background: #111827;
                            color: #f9fafb;
                            padding: 20px;
                            border-radius: 10px;
                            overflow: auto;
                            white-space: pre-wrap;
                        ">{e}</pre>

                        <br>

                        <a href="/dashboard/dresses/">
                            ← Back to Dresses
                        </a>

                    </body>
                    </html>
                    """,
                    status=500
                )

    else:

        form = DressForm(
            user=request.user
        )

    return render(
        request,
        'admin/add_dress.html',
        {
            'form': form
        }
    )


# =========================================================
# ADD MULTIPLE DRESSES
# =========================================================

@login_required(login_url='login')
def add_multiple_dresses(request):
    """Upload multiple images with a real browser-side progress bar.

    The user assigns a category to each image before submitting. The browser
    sends all selected files and category IDs in one XMLHttpRequest so upload
    progress reflects bytes actually sent to the server.
    """
    categories = Category.objects.filter(user=request.user).order_by('name')

    if request.method == 'POST':
        files = request.FILES.getlist('photos')
        max_files = 30
        max_file_size = 12 * 1024 * 1024  # 12 MB per original image
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}

        def fail(message, status=400):
            return JsonResponse({'ok': False, 'error': message}, status=status)

        if not files:
            return fail('Please select at least one photo.')
        if len(files) > max_files:
            return fail(f'You can upload up to {max_files} photos at a time.')
        if not categories.exists():
            return fail('Create a category before uploading dresses.')

        validated = []
        for index, uploaded in enumerate(files):
            extension = Path(uploaded.name).suffix.lower()
            if extension not in allowed_extensions:
                return fail(f'{uploaded.name}: unsupported file type.')
            if uploaded.size > max_file_size:
                return fail(f'{uploaded.name}: file is larger than 12 MB.')

            category_id = request.POST.get(f'category_{index}', '').strip()
            try:
                category = categories.get(pk=int(category_id))
            except (ValueError, TypeError, Category.DoesNotExist):
                return fail(f'Please choose a valid category for {uploaded.name}.')

            # A readable default name based on the filename; no extra fields
            # are required in the bulk workflow.
            original_stem = Path(uploaded.name).stem
            name = original_stem.replace('_', ' ').replace('-', ' ').strip() or 'Untitled Dress'
            # Optional color field for each photo; blank values use "Unknown".
            color = request.POST.get(f'color_{index}', '').strip()
            if len(color) > 50:
                return fail(f'Color for {uploaded.name} must be 50 characters or fewer.')

            validated.append((uploaded, category, name[:150], color or 'Unknown'))

        created_count = 0
        try:
            with transaction.atomic():
                for uploaded, category, name, color in validated:
                    optimized_image = optimize_image(uploaded)
                    dress = Dress(
                        user=request.user,
                        name=name,
                        category=category,
                        description='',
                        color=color,
                        size='One Size',
                    )
                    output_name = f'{slugify(name) or "dress"}.jpg'
                    dress.photo.save(output_name, optimized_image, save=False)
                    dress.save()
                    created_count += 1
        except Exception:
            logger.exception('BULK ADD DRESSES ERROR')
            return fail(
                'Something went wrong while processing the photos. Please try again.',
                status=500,
            )

        return JsonResponse({
            'ok': True,
            'created': created_count,
            'redirect_url': redirect('dashboard_dresses').url,
            'message': f'{created_count} dresses added successfully.',
        })

    return render(request, 'admin/add_multiple_dresses.html', {
        'categories': categories,
        'max_files': 30,
        'max_file_size_mb': 12,
    })


# =========================================================
# EDIT DRESS
# =========================================================

@login_required(login_url='login')
def edit_dress(request, dress_id):

    dress = get_object_or_404(
        Dress,
        id=dress_id,
        user=request.user
    )

    if request.method == 'POST':

        form = DressForm(
            request.POST,
            request.FILES,
            instance=dress,
            user=request.user
        )

        if form.is_valid():

            try:

                dress = form.save(
                    commit=False
                )

                dress.user = request.user

                # ==========================================
                # OPTIMIZE + CONVERT NEW IMAGE TO JPEG
                # ==========================================

                if 'photo' in request.FILES:

                    optimized_image = optimize_image(
                        request.FILES['photo']
                    )

                    original_name = request.FILES['photo'].name

                    base_name = original_name.rsplit(
                        '.',
                        1
                    )[0]

                    dress.photo.save(
                        f"{base_name}.jpg",
                        optimized_image,
                        save=False
                    )

                dress.save()

                return redirect(
                    'dashboard_dresses'
                )

            except Exception as e:

                logger.exception("EDIT DRESS ERROR")

                return HttpResponse(
                    f"""
                    <html>
                    <head>
                        <title>Edit Dress Error</title>
                    </head>

                    <body style="
                        font-family: Arial, sans-serif;
                        padding: 40px;
                        background: #f8fafc;
                    ">

                        <h2 style="
                            color: #dc2626;
                        ">
                            Edit Dress Error
                        </h2>

                        <pre style="
                            background: #111827;
                            color: #f9fafb;
                            padding: 20px;
                            border-radius: 10px;
                            overflow: auto;
                            white-space: pre-wrap;
                        ">{e}</pre>

                        <br>

                        <a href="/dashboard/dresses/">
                            ← Back to Dresses
                        </a>

                    </body>
                    </html>
                    """,
                    status=500
                )

    else:

        form = DressForm(
            instance=dress,
            user=request.user
        )

    return render(
        request,
        'admin/edit_dress.html',
        {
            'form': form,
            'dress': dress,
        }
    )


# =========================================================
# DELETE DRESS
# =========================================================

@login_required(login_url='login')
def delete_dress(request, dress_id):

    dress = get_object_or_404(
        Dress,
        id=dress_id,
        user=request.user
    )

    if request.method == 'POST':

        if dress.photo:
            dress.photo.delete(save=False)

        dress.delete()

        return redirect(
            'dashboard_dresses'
        )

    return render(
        request,
        'admin/delete_dress.html',
        {
            'dress': dress,
        }
    )


# =========================================================
# CATEGORY LIST
# =========================================================

@login_required(login_url='login')
def category_list(request):

    categories = (
        Category.objects
        .filter(user=request.user)
        .order_by('name')
    )

    return render(
        request,
        'admin/categories.html',
        {
            'categories': categories,
        }
    )


# =========================================================
# ADD CATEGORY
# =========================================================

@login_required(login_url='login')
def add_category(request):

    if request.method == 'POST':

        name = request.POST.get(
            'name',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        if name:

            Category.objects.create(
                user=request.user,
                name=name,
                description=description
            )

            return redirect(
                'category_list'
            )

    return render(
        request,
        'admin/add_category.html'
    )


# =========================================================
# EDIT CATEGORY
# =========================================================

@login_required(login_url='login')
def edit_category(request, category_id):

    category = get_object_or_404(
        Category,
        id=category_id,
        user=request.user
    )

    if request.method == 'POST':

        name = request.POST.get(
            'name',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        if name:

            category.name = name
            category.description = description

            category.save()

            return redirect(
                'category_list'
            )

    return render(
        request,
        'admin/edit_category.html',
        {
            'category': category,
        }
    )


# =========================================================
# DELETE CATEGORY
# =========================================================

@login_required(login_url='login')
def delete_category(request, category_id):

    category = get_object_or_404(
        Category,
        id=category_id,
        user=request.user
    )

    if request.method == 'POST':

        category.delete()

        return redirect(
            'category_list'
        )

    return render(
        request,
        'admin/delete_category.html',
        {
            'category': category,
        }
    )


# =========================================================
# FAVORITES
# =========================================================

@login_required(login_url='login')
def toggle_favorite(request, dress_id):

    dress = get_object_or_404(
        Dress,
        id=dress_id,
        user=request.user
    )

    favorite = Favorite.objects.filter(
        user=request.user,
        dress=dress
    ).first()

    if favorite:

        favorite.delete()

    else:

        Favorite.objects.create(
            user=request.user,
            dress=dress
        )

    return redirect(
        request.META.get(
            'HTTP_REFERER',
            'home'
        )
    )


@login_required(login_url='login')
def favorite_list(request):

    favorites = (
        Favorite.objects
        .filter(user=request.user)
        .select_related(
            'dress',
            'dress__category'
        )
        .order_by('-created_at')
    )

    return render(
        request,
        'collection/favorites.html',
        {
            'favorites': favorites,
        }
    )


# =========================================================
# CREATE NEW USER
# =========================================================

def register(request):

    if request.user.is_authenticated:

        return redirect(
            'admin_dashboard'
        )

    if request.method == 'POST':

        username = request.POST.get(
            'username',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        confirm_password = request.POST.get(
            'confirm_password',
            ''
        )

        # =================================================
        # USERNAME VALIDATION
        # =================================================

        if not username:

            messages.error(
                request,
                'Username is required.'
            )

            return redirect(
                'register'
            )

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                'Username already exists.'
            )

            return redirect(
                'register'
            )

        # =================================================
        # PASSWORD VALIDATION
        # =================================================

        if not password:

            messages.error(
                request,
                'Password is required.'
            )

            return redirect(
                'register'
            )

        if password != confirm_password:

            messages.error(
                request,
                'Passwords do not match.'
            )

            return redirect(
                'register'
            )

        if len(password) < 8:

            messages.error(
                request,
                'Password must contain at least 8 characters.'
            )

            return redirect(
                'register'
            )

        # =================================================
        # CREATE USER
        # =================================================

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # =================================================
        # CREATE DEFAULT CATEGORIES
        # =================================================

        create_default_categories(user)

        # =================================================
        # REGISTRATION SUCCESS
        # =================================================

        messages.success(
            request,
            'Account created successfully. Please login.'
        )

        return redirect(
            'login'
        )

    return render(
        request,
        'registration/register.html'
    )


# =========================================================
# LOGOUT
# =========================================================

class CustomLogoutView(LogoutView):

    next_page = 'login'

# =========================================================
# SHARE SELECTED DRESSES (LINK EXPIRES AFTER 24 HOURS)
# =========================================================

@login_required(login_url='login')
def create_dress_share(request):
    """Create a public, view-only gallery containing only selected dresses."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        raw_ids = payload.get('dress_ids', [])
        if not isinstance(raw_ids, list):
            raise ValueError
        ids = list(dict.fromkeys(int(value) for value in raw_ids))
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid selection.'}, status=400)

    if not ids:
        return JsonResponse({'error': 'Select at least one dress photo.'}, status=400)
    if len(ids) > 100:
        return JsonResponse({'error': 'Please share no more than 100 photos at once.'}, status=400)

    dresses = list(Dress.objects.filter(user=request.user, id__in=ids))
    if len(dresses) != len(ids):
        return JsonResponse({
            'error': 'One or more selected dresses were not found in your collection.'
        }, status=400)

    share = DressShare.objects.create(
        owner=request.user,
        expires_at=timezone.now() + timedelta(hours=24),
    )
    share.dresses.set(dresses)
    share_url = request.build_absolute_uri(
        reverse('shared_dress_gallery', kwargs={'token': share.token})
    )
    return JsonResponse({
        'url': share_url,
        'expires_at': share.expires_at.isoformat(),
        'count': len(dresses),
    })


def shared_dress_gallery(request, token):
    """Public recipient page; the token grants view access for 24 hours."""
    share = get_object_or_404(
        DressShare.objects.prefetch_related('dresses__category'),
        token=token,
    )
    if not share.is_active or share.is_expired:
        return render(request, 'collection/share_expired.html', status=410)

    dresses = share.dresses.all().order_by('-created_at')
    if not dresses.exists():
        return render(request, 'collection/share_expired.html', status=410)

    return render(request, 'collection/shared_gallery.html', {
        'share': share,
        'dresses': dresses,
    })


@login_required(login_url='login')
def revoke_dress_share(request, token):
    """Allow the owner to disable a share before its expiry."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)
    share = get_object_or_404(DressShare, token=token, owner=request.user)
    share.is_active = False
    share.save(update_fields=['is_active'])
    return JsonResponse({'success': True})
