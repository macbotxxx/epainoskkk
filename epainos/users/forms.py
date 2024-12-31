from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import forms as admin_forms
from django.forms import EmailField
from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms.widgets import TextInput

from .models import User, Contestant, ContestantImage


FORMAT_CHOICES = (
    ('xls', 'xls'),
    ('csv', 'csv'),
    ('json', 'json'),
)

class FormatForm(forms.Form):
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        # widget=forms.Select(attrs={'class':'form-select'})
    )

class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.UserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class MultipleURLInput(TextInput):
    template_name = 'dashboard/multiple.html'

    def get_context(self, name, value, attrs):
        if value is None:
            value = []
        context = super().get_context(name, value, attrs)
        context['widget']['value'] = value
        return context

    def value_from_datadict(self, data, files, name):
        return data.getlist(name)


class MultipleURLField(forms.URLField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleURLInput())
        super().__init__(*args, **kwargs)

    def clean(self, value):
        # Ensure value is a list
        if not isinstance(value, list):
            value = [value]
        # Clean each URL individually
        cleaned_data = [super().clean(v) for v in value]
        return cleaned_data
    

class ContestantImageForm(forms.ModelForm):
    image = MultipleURLField()
    class Meta:
        model = ContestantImage
        fields = ('image',)


class ContestantProfileForm(forms.ModelForm):
    contestant_image = MultipleFileField()
    contestant_videos = MultipleURLField()

    class Meta:
        model = Contestant
        fields = ('first_name','last_name', 'stage_name', 'contestant_inspiration', 'contestant_image', 'contestant_videos')


class ContestantEditProfileForm(forms.ModelForm):
    contestant_image = MultipleFileField()
    # contestant_videos = MultipleURLField()

    class Meta:
        model = Contestant
        fields = ('first_name','last_name', 'stage_name', 'contestant_inspiration', )


class ContestantVote(forms.Form):
    contestant_id = forms.CharField(widget=forms.HiddenInput())
    number_of_vote = forms.IntegerField()


class ContestantEditProfileForm(forms.ModelForm):
    class Meta:
        model = Contestant
        fields = [
            'contestant_id', 'name', 'first_name', 'last_name',
            'stage_name', 'contestant_inspiration',
            'contestant_videos'
        ]
        widgets = {
            'contestant_videos': forms.Textarea(attrs={'rows': 3}),
        }

    contestant_images = MultipleFileField(required=False)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['contestant_images'].initial = self.instance.contestant_images.all()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
            if self.cleaned_data['contestant_images']:
                images = self.cleaned_data['contestant_images']
                for image in images:
                    img_instance = ContestantImage.objects.create(image=image)
                    instance.contestant_images.add(img_instance)
        return instance
