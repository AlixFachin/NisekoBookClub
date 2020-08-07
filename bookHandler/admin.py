from django.contrib import admin
from .models import AbstractBook, ActualBook, Genre, Author, Transaction, User

admin.site.site_header = 'Niseko Book Club'
admin.site.site_title = 'Niseko Book Club Admin Page'

admin.site.register(AbstractBook)
admin.site.register(Genre)
admin.site.register(Author)
admin.site.register(Transaction)
admin.site.register(User)

@admin.register(ActualBook)
class ActualBookAdmin(admin.ModelAdmin):
    list_display = ('id','get_book_title','created_date', 'owner', 'status')

    def get_book_title(self, actual_book):
        return actual_book.abstract_book.title
    get_book_title.short_description = 'Title'