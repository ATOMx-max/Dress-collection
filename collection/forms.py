from django import forms
from .models import Dress, Category


class DressForm(forms.ModelForm):

    class Meta:
        model = Dress

        fields = [
            'name',
            'photo',
            'description',
            'category',
            'color',
            'size',
        ]

        widgets = {
            'name': forms.TextInput(
                attrs={
                    'placeholder': 'Enter dress name',
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'placeholder': 'Enter dress description',
                    'rows': 5,
                }
            ),

            'color': forms.TextInput(
                attrs={
                    'placeholder': 'Enter color',
                }
            ),

            'size': forms.TextInput(
                attrs={
                    'placeholder': 'Enter size',
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        if user is not None:
            self.fields['category'].queryset = (
                Category.objects
                .filter(user=user)
                .order_by('name')
            )
        else:
            self.fields['category'].queryset = Category.objects.none()

    def clean_category(self):
        category = self.cleaned_data.get('category')

        if category and self.user:
            if category.user != self.user:
                raise forms.ValidationError(
                    'You can only select your own category.'
                )

        return category