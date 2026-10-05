from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Category, Dress, Favorite
from .forms import DressForm
from django.shortcuts import render, get_object_or_404, redirect
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

            dress = form.save(
                commit=False
            )

            dress.user = request.user

            dress.save()

            return redirect(
                'dashboard_dresses'
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