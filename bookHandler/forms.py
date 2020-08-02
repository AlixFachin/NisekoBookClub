from django import forms

class UserBookForm(forms.Form):
    """ this class will be used to edit an actual book in a user-convenient way.
        On the back-end it will create (if necessary) one instance of ActualBook and one instance of AbstractBook, Author etc...
        """
    
    isbn = forms.CharField(max_length=20, required=False)
    title = forms.CharField(max_length=100, required=True,help_text='Enter the book title')
    author = forms.CharField(max_length=50, required=True, help_text='Enter authors separated by commas, last name first')
    genre = forms.CharField(max_length=100, required=False)
    summary = forms.CharField(required=False, widget=forms.Textarea)



