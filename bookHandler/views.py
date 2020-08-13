from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import login, authenticate # In order to login new users after registration

from .models import AbstractBook, ActualBook, Genre, Author, Transaction, Message
from django.contrib.auth.models import User
from .forms import UserBookForm, RegisterForm, TransactionReplyForm, EditTransactionForm, NewMessageForm

from django.utils import timezone
from datetime import datetime, timedelta 

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

@login_required
def profile_view(request):
    # In the profile view we look at the following:
    # a) All the books / inventory of the user
    # b and c) All the history of books lent and borrowed
    # d) User characteristics (pasword, e-mail, ...)
    # e) Other activities (latest reviews, ...)
    personal_inventory = ActualBook.objects.filter(owner=request.user).order_by('-created_date')
    lent_history = Transaction.objects.filter(Q(lender=request.user) & Q(transaction_state__in=[Transaction.INITIAL_REQUEST, Transaction.APPROVED_REQUEST, Transaction.BOOK_LENT])).order_by('transaction_state','-lend_date') 
    borrowed_history = Transaction.objects.filter(Q(borrower=request.user)&Q(transaction_state__in=[Transaction.INITIAL_REQUEST, Transaction.APPROVED_REQUEST])).order_by('transaction_state', '-lend_date')
    transaction_history = Transaction.objects.filter((Q(borrower=request.user)|Q(lender=request.user))
        &Q(transaction_state__in=[Transaction.BOOK_RETURNED, Transaction.REJECTED_REQUEST, Transaction.BOOK_LOST])).order_by('transaction_state', '-lend_date')
    context = {
        'personal_inventory':personal_inventory,
        'lent_history': lent_history, 
        'borrowed_history' : borrowed_history,
        'transaction_history' : transaction_history,
    }
    return render(request, 'bookHandler/user-profile.html', context)

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            raw_password = form.cleaned_data['password1']
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form':form})

@login_required
def new_borrowing_request(request, book_id):
    # the current user logged wants to borrow the given book.
    # We have to check if the book is still available.
    # If everything is OK, we have to create a new transaction in 'request' mode and connect all the dots.
    # In the future, we will be able to send an e-mail of new notification to the lender.
    if request.method == 'POST':
        actualbook = get_object_or_404(ActualBook,id=book_id)
        if actualbook.status == ActualBook.AVAILABLE:
            book_owner = actualbook.owner
            if not book_owner == request.user:
                new_request = Transaction(book=actualbook, lender=book_owner, borrower=request.user, 
                    lend_date=timezone.now() + timedelta(days=7), 
                    return_date=timezone.now() + timedelta(days=37) )
                new_request.transaction_state = Transaction.INITIAL_REQUEST
                new_request.save()
                actualbook.status = ActualBook.UNAVAILABLE # We will put it unavailable until the owner denies the request or the book is given back
                actualbook.save()
                messages.success(request, 'Book successfully borrowed!')
            else:
                messages.warning(request, 'You cannot borrow your own books!')
        else:
            messages.error(request, 'This book is not available')
    else:
        messages.error(request,'Error in the HTTP Request')
    return redirect(actualbook)

@login_required
def reply_request(request, transaction_id):
    # View called by the owner of the book to approve the transaction
    book_transaction = get_object_or_404(Transaction, id=transaction_id)
    if request.user != book_transaction.lender:
        messages.error(request,"You cannot edit a transaction on books you don't own")
        return redirect(request.user)
    
    if request.method == 'POST':
        form = TransactionReplyForm(request.POST)
        if form.is_valid():
            owner_reply = form.cleaned_data['owner_reply']
            if owner_reply=='Yes':
                book_transaction.transaction_state = Transaction.APPROVED_REQUEST
            else:
                book_transaction.transaction_state = Transaction.REJECTED_REQUEST
            book_transaction.save()
            if form.cleaned_data['message'] != '':
                new_message = Message(author=request.user,destination=book_transaction.borrower, transaction=book_transaction,text=form.cleaned_data['message'])
                new_message.save()
            return redirect(request.user)
        else:
            messages.error(request, 'Error in form fields')
            return render(request, 'bookHandler/reply-transaction.html', { 'form':form, 'transaction':book_transaction }) 
    else:
        form = TransactionReplyForm({'owner_reply':'Yes','transaction_id':transaction_id, 'lend_date':book_transaction.lend_date, 'return_date':book_transaction.return_date,})
        new_message_form = NewMessageForm()
        return render(request, 'bookHandler/reply-transaction.html', { 'form':form, 'transaction':book_transaction,  }) 

@login_required
def edit_transaction(request, transaction_id):
    # TO DO-> Initial checks if the current user is not the transaction book owner.
    book_transaction = get_object_or_404(Transaction, id=transaction_id)
    if request.user != book_transaction.lender:
        messages.error(request,"You cannot edit a transaction on books you don't own")
        return redirect(request.user)

    if request.method == 'POST':
        form = EditTransactionForm(request.POST)
        book_transaction = get_object_or_404(Transaction, id=transaction_id)
        if form.is_valid():   
            book_transaction.lend_date = form.cleaned_data['lend_date']
            book_transaction.return_date = form.cleaned_data['return_date']
            book_transaction.transaction_state = form.cleaned_data['transaction_state']
            book_transaction.save()
            # Looking at the comment
            if form.cleaned_data['new_message'] != '':
                new_message = Message(author=request.user,destination=book_transaction.borrower, transaction=book_transaction,text=form.cleaned_data['new_message'])
                new_message.save()
            return redirect(request.user)
        else:
            return render(request, 'bookHandler/edit-transaction.html', {'transaction': book_transaction, 'transaction_form':form })            
    else:
        book_transaction = get_object_or_404(Transaction, id=transaction_id)
        form = EditTransactionForm(instance=book_transaction)

        return render(request, 'bookHandler/edit-transaction.html', {'transaction': book_transaction, 'transaction_form':form })

@login_required
def view_conversation(request, transaction_id):
    book_transaction = get_object_or_404(Transaction, id=transaction_id)
    if request.user != book_transaction.lender and request.user != book_transaction.borrower:
        messages.error(request, "You cannot view a conversation related to a transaction you are not participating into")
        return redirect('bookHandler:home')
    
    if request.method == 'POST':
        form = NewMessageForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['message_text'] != '':
                new_message = Message(author=request.user,destination=book_transaction.borrower, transaction=book_transaction,text=form.cleaned_data['message_text'])
                new_message.save()
    
    form = NewMessageForm()
    message_list = Message.objects.filter(transaction=transaction_id).all()
    return render(request, 'bookHandler/view-conversation.html', {'transaction': book_transaction, 'message_list':message_list, 'new_message_form':form, })