from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import AbstractBook, ActualBook, Genre, Author, Transaction
from django.contrib.auth.models import User
from .forms import UserBookForm

# Create your views here.

def book_index(request):
    all_book_list = AbstractBook.objects.all()
    book_list_with_author = []
    for book in all_book_list:
        book_list_with_author.append( (book,','.join([str(author) for author in book.author.all()])) )
    return render(request, 'bookHandler/books-index.html', {'book_list_with_author': book_list_with_author })

# Main view: List of all actual books available, including user name
def home_view(request):
    pass

# Detailed view of an actual book: Details about the abstract book, the status / quality of the actual book, details about the user and list of transactions
def abstract_detailed_view(request, book_id):
    abstract_book = AbstractBook.objects.get(id=book_id)
    # TO DO - look at case when the book doesn't exist
    genre_list = abstract_book.genre.all()
    actual_list = abstract_book.instances.all()
    author_list = abstract_book.author.all()

    context = { 'book' : abstract_book, 
        'actual_list' : actual_list ,
        'genre_list' : genre_list,
        'author_list' : author_list,
        }
    return render(request, 'bookHandler/detailed-abstract-book.html', context)


def actualBook_detailed_view(request, book_id):
    actual_book = get_object_or_404(ActualBook, id=book_id)
    abstract_book = actual_book.abstract_book
    transaction_list = actual_book.transactions.all()

    context= {
        'actual_book' : actual_book,
        'abstract_book' : abstract_book,
        'transaction_list' : transaction_list,
    }

    return render(request, 'bookHandler/detailed-actual-book.html', context )


# User profile: User data, then tabbed view of past lent books, past borrowed books, and edit inventory (add books / edit)
def profile_view(request, user_id):
    pass

# Showing the author profile, a bio, a list of books (and availability of some stuff)
def author_detailed_view(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    book_list = AbstractBook.objects.filter(author=author)
    context = { 'author' : author, 'book_list' : book_list }

    return render(request, 'bookHandler/detailed-author.html', context)


@login_required
def add_book_view(request):
    if request.method == 'POST':
        # We need to parse the content of the fields and then create if needed various instances
        newBookForm = UserBookForm(request.POST)
        if newBookForm.is_valid():
            # Check if the abstract book already exists
            author_list_string = newBookForm.cleaned_data['author'].split(',')
            new_abstract_book = AbstractBook.get_or_create(newBookForm.cleaned_data['title'],author_list_string)
            # Now we create a new Actual Book
            new_actual_book = ActualBook()
            new_actual_book.abstract_book = new_abstract_book
            new_actual_book.owner = request.user
            new_actual_book.save()
            return redirect('bookHandler:index')
        else:
            return redirect('bookHandler:index')
    else:
        newForm = UserBookForm()
        return render(request,'bookHandler/new-book-form.html', { 'form' : newForm}  )