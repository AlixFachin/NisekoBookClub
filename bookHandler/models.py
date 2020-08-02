from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils import timezone
from django.conf import settings # for the settings.AUTH_USER_MODEL

# Create your models here.

class User(AbstractUser):
    AREA_LOCATIONS = (
        ('nh', 'Higashiyama (Niseko-cho)'),
        ('nt', 'Niseko-cho town'),
        ('nk', 'Kondo Niseko-cho'),
        ('kh', 'Hirafu (Kutchan-cho)'),
        ('kk', 'Kabayama (Kutchan-cho)'),
        ('kt', 'Kutchan town center'),
        ('oo', 'Others'),
    )
    location = models.TextField(max_length=2, choices=AREA_LOCATIONS, default='nt')

class Genre(models.Model):
    """ Model representing a book genre """
    name = models.CharField(max_length=200, help_text='Enter a book genre(e.g. crime, historical fiction, ...')
    # To Do: a foreignkey to self in order to point to the various translated fields. 
    # Then a method to translate into a language would return the proper translation, or the original value if not translated yet
    # (And ideally do an admin method in order to see what needs to be translated)

    def __str__(self):
        return self.name

class AbstractBook(models.Model):
    """ Model represents a generic book, not an actual physical book """
    title = models.CharField(max_length=200)
    author = models.ManyToManyField('Author')
    summary = models.TextField(max_length=1000, help_text='Enter a quick description for the model')
    isbn = models.CharField('ISBN', max_length=13, help_text='International code (10 or 13 digits)')
    genre = models.ManyToManyField(Genre, help_text='Select one or many genres for this book')

    def __str__(self):
        return self.title

    @staticmethod
    def get_or_create(title, author_list_string, book_summary=''):
        """
        get_or_create will look for the corresponding book and create it, if not found.
        title: String with the book title
        author_list_string: A list of strings containing Author names, preferably with LAST NAME first (e.g. Einstein Albert)
        book_summary: An (optional) string with the summary
        """
        author_list = []
        for author_string in author_list_string:
            new_author = Author.get_or_create(author_string)
            author_list.append(new_author)

        query_filters = models.Q()
        if title != '':
            query_filters &= models.Q(title=title)
        results = AbstractBook.objects.filter(query_filters)
        for author in author_list:
            # We supposed that the string is well constructed with LAST
            query_filters = models.Q(author__last_name=author.last_name) & models.Q(author__first_name=author.first_name)
            results = results.filter(query_filters) # We chain the filter instead of the Qs because of the ManyToMany relationship

        if len(results) == 0:
            new_book = AbstractBook(title=title, summary=book_summary, isbn='')
            new_book.save() # The author 'ManyToMany' needs the object to be created in order to allow an author to be added
            for author in author_list:
                new_book.author.add(author)
            new_book.save()
            return new_book
        else:
            return results[0]

class ActualBook(models.Model):
    """ Model will represent an actual physical book, owned by someone and on the lend/borrow market """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID for this actual book' )
    abstract_book = models.ForeignKey(AbstractBook, on_delete=models.CASCADE, related_name='instances')
    created_date = models.DateField(editable=False, default=timezone.now)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, default=1, related_name='book_inventory')
    BOOK_STATUS = (
        ('a', 'Available'),
        ('u', 'Unavailable'), # Not borrowed but lost, damaged or owner wants to remove from the market
        ('o', 'Out for lent'),
    )
    status = models.CharField(max_length=1, choices=BOOK_STATUS, default='a')

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return '%s - %s (%s)' % (self.abstract_book.title,self.abstract_book.author,self.id)

class Author(models.Model):
    """ Model represents the list of authors """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.TextField(max_length=500, default='', null=True, verbose_name='biography')
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def get_absolute_url(self):
        pass
    
    def __str__(self):
        return '%s %s' % (self.last_name, self.first_name)

    @staticmethod
    def get_or_create(author):
        #First, assume last name first 
        last_name = author.split()[0].title()
        if len(author)>len(last_name):
            first_name = author[len(last_name)+1:].title()
        else:
            first_name = ''
        queryset_and = Author.objects.filter(first_name__iexact=first_name) & Author.objects.filter(last_name__iexact=last_name)
        if len(queryset_and) == 0:
            # Author not found - trying to reverse first and last name
            last_name_2 = author.split()[-1].title()
            if len(author)>len(last_name_2):
                first_name_2 = author[:len(author)-len(last_name_2)].title().strip()
            else:
                first_name_2 = ''
            queryset_and = Author.objects.filter(first_name__iexact=first_name_2) & Author.objects.filter(last_name__iexact=last_name_2)            
            if len(queryset_and) == 0:
                # Giving up - have to create a new author
                # Using the initial variables (last_name, first_name) as they correspond to the LAST NAME FIRST convention (e.g. Einstein Albert)
                new_author = Author(last_name=last_name, first_name=first_name)
                new_author.save()
                return new_author
            else:
                return queryset_and[0]
        else:
            return queryset_and[0]
        
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID for the transaction')
    book = models.ForeignKey(ActualBook, on_delete=models.CASCADE,related_name='transactions')
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='transactions')
    lend_date = models.DateField(default=timezone.now)
    return_date = models.DateField(default=timezone.now)

    TRANSACTION_TYPE = (
        ('i', 'Initial Transaction'),
        ('e', 'Extension'),
    )
    transaction_type = models.CharField(max_length=1, choices=TRANSACTION_TYPE, default='i')

    class Meta:
        ordering=['-lend_date']

    def __str__(self):
        return '%s on %s btw %s and %s' % (self.book, self.lend_date, self.book.owner, self.borrower)