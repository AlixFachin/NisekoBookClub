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
    path('user_profile',views.profile_view, name='user_profile'),
    path('new_transaction/<uuid:book_id>', views.new_borrowing_request, name='new_transaction'),
    path('reply_transaction/<uuid:transaction_id>',views.reply_request, name='reply_transaction'),
    path('edit_transaction/<uuid:transaction_id>', views.edit_transaction, name='edit_transaction'),
    path('view_conversation/<uuid:transaction_id>', views.view_conversation, name='view_conversation'),
]