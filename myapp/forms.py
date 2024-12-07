from django import forms
from .models import Request, Street, RepairType, RepairDetail, User
#from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
import logging

logger = logging.getLogger(__name__)

class RequestForm(forms.ModelForm):
    no_middle_name = forms.BooleanField(required=False, label='Нет отчества', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Request
        fields = [
            'category', 'primary_repair_type', 'secondary_repair_type', 'first_name',
            'last_name', 'middle_name', 'no_middle_name', 'short_description', 'street', 'building',
            'room', 'contact_phone', 'email', 'description'
        ]
        labels = {
            'category': 'Категория',
            'primary_repair_type': 'Вид ремонта',
            'secondary_repair_type': 'Подробности',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'middle_name': 'Отчество',
            'no_middle_name': 'Нет отчества',
            'short_description': 'Краткое описание проблемы',
            'street': 'Улица',
            'building': 'Здание',
            'room': 'Помещение',
            'contact_phone': 'Контактный телефон',
            'email': 'Адрес электронной почты',
            'description': 'Описание проблемы',
        }
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'primary_repair_type': forms.Select(attrs={'class': 'form-control'}),
            'secondary_repair_type': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.Select(attrs={'class': 'form-control'}),
            'building': forms.TextInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_contact_phone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)

        # Set required fields
        self.fields['category'].required = True
        self.fields['primary_repair_type'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['short_description'].required = True
        self.fields['street'].required = True
        self.fields['building'].required = True
        self.fields['room'].required = True
        self.fields['contact_phone'].required = True
        self.fields['email'].required = True

        # Non-required fields
        self.fields['middle_name'].required = False
        self.fields['description'].required = False
        self.fields['secondary_repair_type'].required = False

        self.fields['street'].queryset = Street.objects.all()
        self.fields['street'].empty_label = None

        if category:
            self.fields['primary_repair_type'].queryset = RepairType.objects.filter(category=category)
        else:
            self.fields['primary_repair_type'].queryset = RepairType.objects.none()

        self.fields['secondary_repair_type'].queryset = RepairDetail.objects.none()

        if 'primary_repair_type' in self.data:
            try:
                repair_type_id = int(self.data.get('primary_repair_type'))
                self.fields['secondary_repair_type'].queryset = RepairDetail.objects.filter(
                    repair_type_id=repair_type_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.primary_repair_type:
            self.fields['secondary_repair_type'].queryset = self.instance.primary_repair_type.repairdetail_set.order_by(
                'name')

    def clean(self):
        cleaned_data = super().clean()
        primary_repair_type = cleaned_data.get('primary_repair_type')
        secondary_repair_type = cleaned_data.get('secondary_repair_type')
        middle_name = cleaned_data.get('middle_name')
        no_middle_name = cleaned_data.get('no_middle_name')

        if primary_repair_type and RepairDetail.objects.filter(repair_type=primary_repair_type).exists() and not secondary_repair_type:
            self.add_error('secondary_repair_type', 'This field is required.')

        # Обработка поля отчества и флага "Нет отчества"
        if no_middle_name:
            cleaned_data['middle_name'] = ''
            self.fields['middle_name'].required = False
        elif not middle_name:
            self.add_error('middle_name', 'Это поле обязательно, если не указано "Нет отчества".')

        return cleaned_data

class UserRegForm(UserCreationForm):
    first_name = forms.CharField(required=True, label='Имя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-control'}))
    middle_name = forms.CharField(required=True, label='Отчество', widget=forms.TextInput(attrs={'class': 'form-control'}))
    no_middle_name = forms.BooleanField(required=False, label='Нет отчества', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    phone_number = forms.CharField(required=True, label='Номер телефона', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, label='Электронная почта', widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'middle_name', 'no_middle_name', 'phone_number', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'no_middle_name' in self.data and self.data['no_middle_name'] == 'on':
            self.fields['middle_name'].required = False

    def clean(self):
        cleaned_data = super().clean()
        middle_name = cleaned_data.get('middle_name')
        no_middle_name = cleaned_data.get('no_middle_name')

        if no_middle_name:
            cleaned_data['middle_name'] = ''
            self.fields['middle_name'].required = False
        elif not middle_name:
            self.add_error('middle_name', 'Это поле обязательно, если не указано "Нет отчества".')

        return cleaned_data

"""class UserRegForm(UserCreationForm):
    CATEGORY_CHOICES = [
        ('small_repair', 'Мелкий ремонт'),
        ('sub_work', 'Подсобные работы'),
        ('warehouse', 'Склад'),
    ]

    middle_name = forms.CharField(required=False, label='Отчество', widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(required=False, label='Номер телефона', widget=forms.TextInput(attrs={'class': 'form-control'}))
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, label='Категория', required=False, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'middle_name', 'phone_number', 'category', 'password1', 'password2']
"""

class CustomUserChangeForm(UserChangeForm):
    CATEGORY_CHOICES = [
        ('small_repair', 'Мелкий ремонт'),
        ('sub_work', 'Подсобные работы'),
        ('warehouse', 'Склад'),
    ]

    middle_name = forms.CharField(required=False, label='Отчество', widget=forms.TextInput(attrs={'class': 'form-control'}))
    no_middle_name = forms.BooleanField(required=False, label='Нет отчества', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    phone_number = forms.CharField(required=False, label='Номер телефона', widget=forms.TextInput(attrs={'class': 'form-control'}))
    category = forms.ChoiceField(required=False, choices=CATEGORY_CHOICES, label='Категория', widget=forms.Select(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, label='Имя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, label='Электронная почта', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(required=True, label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'middle_name', 'no_middle_name', 'phone_number', 'category', 'email']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Получаем текущего пользователя
        super().__init__(*args, **kwargs)

        # Устанавливаем видимость поля "Категория" только для операторов
        if user and user.groups.filter(name='Оператор').exists() and not user.is_superuser:
            self.fields['category'].widget.attrs['style'] = 'display:block;'
        else:
            self.fields['category'].widget.attrs['style'] = 'display:none;'

        if not self.instance.middle_name:
            self.fields['no_middle_name'].initial = True
            self.fields['middle_name'].required = False

    def clean(self):
        cleaned_data = super().clean()
        middle_name = cleaned_data.get('middle_name')
        no_middle_name = cleaned_data.get('no_middle_name')

        if no_middle_name:
            cleaned_data['middle_name'] = ''
            self.fields['middle_name'].required = False
        elif not middle_name:
            self.add_error('middle_name', 'Это поле обязательно, если не указано "Нет отчества".')

        return cleaned_data
class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']
