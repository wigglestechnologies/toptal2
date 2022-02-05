from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from accounts.models import Account

class AccountCreationForm(forms.ModelForm):
    
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = ('email',)

    def clean_password2(self):
        
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        
        return password2

    def save(self, commit=True):
        
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        
        if commit:
            user.save()
        
        return user


class AccountChangeForm(forms.ModelForm):
    
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Account
        fields = ('email', 'password', 'is_active', 'is_admin',)

    def clean_password(self):        
        return self.initial["password"]
    
class AccountAdmin(UserAdmin):
    
    form = AccountChangeForm
    add_form = AccountCreationForm

    list_display    = ('first_name', 'last_name', 'email', 'last_login', 'is_admin',)
    search_fields   = ('email', 'first_name', 'last_name')
    readonly_fields = ('id', 'date_joined', 'last_login')
    ordering        =  ('first_name', 'last_name')        
    
    fieldsets = (
        (None, {'fields' : ('first_name', 'last_name', 'email', 'last_login', 'is_admin')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide', ), 
            'fields' : (
                'first_name', 
                'last_name', 
                'email', 
                'password1', 
                'password2',                 
                'is_staff',
                'is_admin'),
        }),
    )

    filter_horizontal   = ()
    list_filter         = ()
    fieldsets           = ()

admin.site.register(Account, AccountAdmin)
    