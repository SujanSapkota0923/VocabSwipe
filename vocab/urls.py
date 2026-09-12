from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('explore/', views.explore_view, name='explore'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup_view, name='signup'),

    path('lists/<int:list_id>/settings/', views.list_settings_view, name='list_settings'),
    path('lists/<int:list_id>/visibility/', views.toggle_public_view, name='toggle_public'),
    path('lists/<int:list_id>/delete/', views.delete_list_view, name='delete_list'),
    path('lists/<int:list_id>/leave/', views.leave_list_view, name='leave_list'),

    path('game/', views.game_view, name='game'),

    path('api/cards/', views.card_list_api, name='card_list_api'),
    path('api/lists/', views.list_word_lists_api, name='list_word_lists_api'),
    path('api/cards/<int:card_id>/status/', views.update_card_status_api, name='update_card_status_api'),
]
