from django.urls import path
from django.contrib.auth.views import LoginView

from . import views


urlpatterns = [

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'dress/<int:dress_id>/',
        views.dress_detail,
        name='dress_detail'
    ),

    # Login
    path(
        'login/',
        LoginView.as_view(
            template_name='registration/login.html',
            redirect_authenticated_user=True,
        ),
        name='login'
    ),

    # Dashboard
    path(
        'dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    # Dresses
    path(
        'dashboard/dresses/',
        views.dashboard_dresses,
        name='dashboard_dresses'
    ),

    path(
        'dashboard/dresses/add/',
        views.add_dress,
        name='add_dress'
    ),

    path(
        'dashboard/dresses/<int:dress_id>/edit/',
        views.edit_dress,
        name='edit_dress'
    ),

    path(
        'dashboard/dresses/<int:dress_id>/delete/',
        views.delete_dress,
        name='delete_dress'
    ),

    # Categories
    path(
        'dashboard/categories/',
        views.category_list,
        name='category_list'
    ),

    path(
        'dashboard/categories/add/',
        views.add_category,
        name='add_category'
    ),

    path(
        'dashboard/categories/<int:category_id>/edit/',
        views.edit_category,
        name='edit_category'
    ),

    path(
        'dashboard/categories/<int:category_id>/delete/',
        views.delete_category,
        name='delete_category'
    ),

    # Logout
    path(
        'logout/',
        views.CustomLogoutView.as_view(),
        name='logout'
    ),
    path(
    'register/',
    views.register,
    name='register'
),
    path(
    'favorite/<int:dress_id>/',
    views.toggle_favorite,
    name='toggle_favorite'
),
    path(
    'favorites/',
    views.favorite_list,
    name='favorite_list'
),
]