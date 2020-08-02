from django.contrib import admin
from .models import AbstractBook, ActualBook, Genre, Author, Transaction, User

admin.site.site_header = 'Niseko Book Club'
admin.site.site_title = 'Niseko Book Club Admin Page'

admin.site.register(AbstractBook)
admin.site.register(ActualBook)
admin.site.register(Genre)
admin.site.register(Author)
admin.site.register(Transaction)
admin.site.register(User)

