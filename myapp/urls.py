from django.urls import path, re_path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView, TokenVerifyView
)
app_name = 'myapp'

urlpatterns = [
    path('login/', views.user_login, name='login'),  
    path('', views.index, name='index'),
    path('news/', views.news_page, name='news_page'),
    path('news/add/', views.add_news, name='add_news'),
    path('news/<int:news_id>/edit/', views.edit_news, name='edit_news'),
    path('news/<int:news_id>/delete/', views.delete_news, name='delete_news'),
    path('excel/', views.excel, name='excel'),
    path('send-email/', views.send_email, name='send_email'),
    path('rent_book/', views.rent_book, name='rent_book'),
    path('blacklist/', views.blacklist, name='blacklist'),
    path('view_returned_books/', views.view_returned_books, name='view_returned_books'),
    path('logout/', views.logout, name='logout'),
    path('pgregister/', views.reg, name='reg'),
    path('add_book/', views.add_book, name='add_book'),
    path('add_publish/', views.add_publish, name='add_publish'),
    path('rent_book/return/<int:publish_id>/book', views.return_book, name='return_book'),
    path('edit/<int:id>/book/', views.edit_book, name='edit_book'),
    path('delete_books/', views.delete_books, name='delete_books'),
    path('select_all_books/', views.select_all_books, name='select_all_books'),
    path('check-isbn/', views.check_isbn, name='check_isbn'),
    path("generate/", views.generate_and_download_barcodes, name="generate_barcodes"),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/school/books/', views.api_school_books, name='api_school_books'),
    path('api/school/borrows/', views.api_school_borrows, name='api_school_borrows'),
]

