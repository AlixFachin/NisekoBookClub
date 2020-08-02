# urls for the bookHandler app
from . import views
from django.urls import path

app_name='bookHandler'
urlpatterns=[
    path('', views.book_index, name='index'),
    path('detail/<int:book_id>/', views.abstract_detailed_view, name='detail_abstract'),
    path('detail_actual/<uuid:book_id>/', views.actualBook_detailed_view, name='detail_actual'),
    path('author/<int:author_id>/', views.author_detailed_view, name='detail_author'),
    path('new_book', views.add_book_view, name='add_book'),
]