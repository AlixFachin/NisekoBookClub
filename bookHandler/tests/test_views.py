from django.test import TestCase

from bookHandler.models import AbstractBook, ActualBook, Author, Genre, User, Transaction
from django.utils import timezone
from datetime import datetime, timedelta

class test_model_methods(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_get_or_create_author(self):
        test_author = Author(last_name='Authorlastname', first_name='Authorfirstname')
        test_author.save()
        test_author2 = Author.get_or_create('Authorlastname Authorfirstname')
        self.assertEquals(test_author2, test_author)
        self.assertEquals(test_author2.first_name,'Authorfirstname') # No camel case in family names
        self.assertEquals(test_author2.last_name, 'Authorlastname')

        test_author3 = Author.get_or_create('Lastname Firstname')
        self.assertEquals(test_author3.first_name,'Firstname')
        self.assertEquals(test_author3.last_name,'Lastname')

        original_author=Author(last_name='Murakami', first_name='Haruki')
        original_author.save()
        before_creation_nr_authors = len(Author.objects.all())
        new_author = Author.get_or_create('Murakami Haruki')
        self.assertEquals(new_author, original_author,msg="New Author creates a new object where it shouldn't")
        self.assertEquals(len(Author.objects.all()), before_creation_nr_authors)
        new_author = Author.get_or_create('MURAKAMI HARUKI')
        self.assertEquals(new_author, original_author, msg='Author get_or_create has issue with case testing')
        new_author = Author.get_or_create('Haruki Murakami')
        self.assertEquals(new_author, original_author, msg='Unable to swap author first and last name')
        new_author = Author.get_or_create('James M. Barrie')
        new_length = len(Author.objects.all())
        self.assertEquals(new_length,before_creation_nr_authors+1)
        new_author = Author.get_or_create('James M. Barrie')
        new_length = len(Author.objects.all())
        self.assertEquals(new_length,before_creation_nr_authors+1)
    
    def test_get_or_create_abstract_book(self):
        # Test of creating one book with one author
        nr_books = len(AbstractBook.objects.all())
        new_book = AbstractBook.get_or_create(title='Memoirs of a Geisha',author_list_string=['Golding Arthur'])
        self.assertEquals(len(AbstractBook.objects.all()),nr_books+1, 'Fail to create a new book through get_or_create // collection length mismatch')
        new_book2 = AbstractBook.get_or_create(title='Memoirs of a Geisha',author_list_string=['Golding Arthur'])
        self.assertEquals(len(AbstractBook.objects.all()),nr_books+1, 'Fail to create a new book through get_or_create // collection length mismatch')
        self.assertEquals(new_book2.title,'Memoirs of a Geisha')
        self.assertEquals(len(new_book2.author.all()),1)
        self.assertEquals(new_book2.author.all()[0].first_name,'Arthur')
        self.assertEquals(new_book2.author.all()[0].last_name,'Golding')

        # Test of creating one book with two authors. 
        nr_books = len(AbstractBook.objects.all())
        new_book = AbstractBook.get_or_create(title='Memoirs of a Geisha',author_list_string=['Lastname1 Firstname1', 'Lastname2 Firstname2'])
        # Testing for the creation of a new book. Same title than above but different authors.
        self.assertEquals(len(AbstractBook.objects.all()),nr_books+1, 'Fail to create a new book through get_or_create // When there are several authors')
        new_book2 = AbstractBook.get_or_create(title='Memoirs of a Geisha',author_list_string=['Lastname1 Firstname1', 'Lastname2 Firstname2'])
        self.assertEquals(len(AbstractBook.objects.all()),nr_books+1, 'Fail to create a new book through get_or_create // Retrieving a newly created book with several authors')
        self.assertEquals(new_book2.title,'Memoirs of a Geisha')
        self.assertEquals(len(new_book2.author.all()),2)
        self.assertEquals(new_book2.author.all()[0].first_name,'Firstname1')
        self.assertEquals(new_book2.author.all()[0].last_name,'Lastname1')
        self.assertEquals(new_book2.author.all()[1].first_name,'Firstname2')
        self.assertEquals(new_book2.author.all()[1].last_name,'Lastname2')

class test_transactions(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 = User.objects.create_user(username='testuser1', password='gluglu1')
        user2 = User.objects.create_user(username='testuser2', password='gluglu2')
        abs_book = AbstractBook.get_or_create(title='Memoirs of a Geisha', author_list_string=['Lastname Firstname'])
        abs_book2 = AbstractBook.get_or_create(title='Special Relativity', author_list_string=['Albert Einstein'])
        real_book = ActualBook.objects.create(abstract_book=abs_book, owner=user1)
        real_book.save()
        real_book = ActualBook.objects.create(abstract_book=abs_book, owner=user2)
        real_book.save()
        actual_2 = ActualBook.objects.create(abstract_book=abs_book2, owner=user1)
        real_book.save()
        # Creating transactions for the books
        old_transaction = Transaction(book=actual_2, lender=user1, borrower=user2, transaction_state=Transaction.BOOK_RETURNED,lend_date=timezone.now() + timedelta(days=-60), 
                    return_date=timezone.now() + timedelta(days=-30),modified_timestamp=timezone.now()+timedelta(days=-30) )
        old_transaction.save()
        new_transaction = Transaction(book=actual_2, lender=user1, borrower=user2, transaction_state=Transaction.INITIAL_REQUEST)
        actual_2.status = ActualBook.OUT_FOR_RENT
        actual_2.save()
        new_transaction.save()

    def test_my_books_view(self):
        login1 = self.client.login(username='testuser1', password='gluglu1')
        response = self.client.get('/bookhandler/my_books')
        self.assertEquals(response.status_code, 200)
        rep_book_list = response.context['book_list']
        self.assertEquals(len(rep_book_list),2)
        (firstBook, firstTrans) = rep_book_list[0]
        (secondBook, secondTrans) = rep_book_list[1]
        self.assertEquals(firstBook.abstract_book.title,'Memoirs of a Geisha')
        self.assertEquals(secondBook.abstract_book.title,'Special Relativity')
        self.assertIsNone(firstTrans)
        self.assertIsNotNone(secondTrans)
        self.assertEquals(secondTrans.book, secondBook)
        self.assertEquals(secondTrans.transaction_state, Transaction.INITIAL_REQUEST)
        self.client.logout()
        response = self.client.get('/bookhandler/my_books')
        self.assertEquals(response.status_code, 302)

    def test_my_requests_view(self):
        # Not logged in
        self.client.logout()
        response = self.client.get('/bookhandler/my_requests')
        self.assertEquals(response.status_code, 302)
        # Logged in but no transaction
        self.client.login(username='testuser1', password='gluglu1')
        response = self.client.get('/bookhandler/my_requests')
        self.assertEquals(response.status_code, 200)
        transaction_list = response.context['transaction_list']
        self.assertEquals(len(transaction_list),0)
        # Logged in -> check that only ACTIVE transactions appear
        self.client.logout()
        self.client.login(username='testuser2', password='gluglu2')
        response = self.client.get('/bookhandler/my_requests')
        self.assertEquals(response.status_code, 200)
        transaction_list = response.context['transaction_list']
        self.assertEquals(len(transaction_list),1)
        self.assertEquals(transaction_list[0].book.abstract_book.title,'Special Relativity')
        self.assertEquals(transaction_list[0].lender.username,'testuser1')
        self.assertEquals(transaction_list[0].borrower.username,'testuser2')




