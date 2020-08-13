from django import forms
from django.contrib.auth.forms import UserCreationForm
from bookHandler.models import User, Transaction

class UserBookForm(forms.Form):
    """ this class will be used to edit an actual book in a user-convenient way.
        On the back-end it will create (if necessary) one instance of ActualBook and one instance of AbstractBook, Author etc...
        """
    
    isbn = forms.CharField(max_length=20, required=False)
    title = forms.CharField(max_length=100, required=True,help_text='Enter the book title')
    author = forms.CharField(max_length=50, required=True, help_text='Enter authors separated by commas, last name first')
    genre = forms.CharField(max_length=100, required=False)
    summary = forms.CharField(required=False, widget=forms.Textarea)

class RegisterForm(UserCreationForm):
    """ Extends the basic User Creation Form with supplementary fields """
    first_name = forms.CharField(max_length=30,required=False)
    last_name = forms.CharField(max_length=30,required=False)
    email = forms.EmailField(max_length=254,help_text='Required. Please input a valid e-mail address')

    class Meta:
        model = User
        fields = ('username','first_name','last_name','email', 'password1','password2', 'location')

class TransactionReplyForm(forms.Form):
    """ Form used by a book owner to reply to incoming requests. (reply with yes or no) """
    REPLY_CHOICES = [('Yes','Accept to lend the book'), ('No','Refuse to lend the book')]
    owner_reply = forms.ChoiceField(choices=REPLY_CHOICES, widget=forms.RadioSelect())
    lend_date = forms.DateField()
    return_date = forms.DateField()
    transaction_id = forms.UUIDField(widget=forms.HiddenInput)
    message = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'class':'form-control'}) )

    class Meta:
        fields = ('owner_reply', 'lend_date', 'return_date', 'message')

class EditTransactionForm(forms.ModelForm):

    new_message = forms.CharField(max_length=500, required=False,help_text='Enter an optional answer', widget=forms.Textarea)

    class Meta:
        model = Transaction
        fields = ['lend_date', 'return_date', 'transaction_state', 'new_message']
    
    def __init__(self, *args, **kwargs):
        super(EditTransactionForm,self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if self.fields[field].widget.__class__.__name__ in ('AdminTextInputWidget' , 'Textarea' ,'TextInput', 'NumberInput' , 'AdminURLFieldWidget', 'Select'):
                self.fields[field].widget.attrs.update({ 'class': 'form-control' })

class NewMessageForm(forms.Form):

    message_text = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'class':'form-control'}) )

