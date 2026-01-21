from django.urls import path
from . import views


urlpatterns = [
    path('', views.upload_view, name='upload'),
    path('delete-list/<int:list_id>/', views.delete_list_view, name='delete_list'),
    path('game/', views.game_view, name='game'),
    path('api/cards/', views.card_list_api, name='card_list_api'),
    path('api/lists/', views.list_word_lists_api, name='list_word_lists_api'),
    path('api/cards/<int:card_id>/status/', views.update_card_status_api, name='update_card_status_api'),
]
