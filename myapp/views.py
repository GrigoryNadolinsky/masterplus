from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm, PasswordChangeForm
from .models import Request
from .forms import RequestForm
from django.core.mail import send_mail
from django.conf import settings
from .decorators import admin_required, operator_required, performer_required, observer_required
from django.http import JsonResponse
#from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from .models import Request, Street, RepairType, RepairDetail, User
from django.db import models
from .forms import UserRegForm, CustomUserChangeForm, CustomAuthenticationForm
from django.urls import reverse


def index(request):
    return render(request, 'myapp/index.html')


def register(request):
    if request.method == 'POST':
        form = UserRegForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Проверяем и создаем группу "New Users" при необходимости
            new_users_group, created = Group.objects.get_or_create(name='New Users')

            # Добавляем пользователя в эту группу
            user.groups.add(new_users_group)

            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт успешно создан!')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Ошибка в поле {field}: {error}")
            messages.error(request, 'Форма содержит ошибки. Пожалуйста, исправьте их и попробуйте снова.')
    else:
        form = UserRegForm()
    return render(request, 'myapp/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Исполнитель').exists() and (
                not request.user.first_name or not request.user.last_name):
            messages.error(request, 'Пожалуйста, заполните поля "Имя" и "Фамилия" перед продолжением работы!')
            return redirect('profile_edit')
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль.')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'myapp/login.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user

    # Проверка обязательных полей для группы "Исполнители"
    if user.groups.filter(name='Исполнитель').exists():
        required_fields = ['username', 'first_name', 'last_name', 'email']
        missing_fields = [field for field in required_fields if not getattr(user, field)]

        if missing_fields:
            if not any(
                    msg.message == 'Пожалуйста, заполните все обязательные поля перед продолжением работы!' for msg in
                    messages.get_messages(request)):
                messages.error(request, 'Пожалуйста, заполните все обязательные поля перед продолжением работы!')
                return redirect('profile_edit')

    # Проверка на принадлежность к группе "New Users"
    is_new_user = user.groups.filter(name='New Users').exists()

    requests = Request.objects.all()
    performer_default = None
    if user.groups.filter(name='Исполнитель').exists() and not request.GET.get('assigned_performer'):
        performer_default = user.id

    is_operator_or_admin = user.groups.filter(name='Оператор').exists() or user.is_superuser
    assigned_performer = request.GET.get('assigned_performer', 'none' if is_operator_or_admin else None)

    # Логика для определения фильтрации по категории
    category = request.GET.get('category')
    use_profile_category = False

    if category is None:  # Если категория не выбрана в фильтре, используем категорию из профиля
        category = user.category
        use_profile_category = True
    elif category == "":  # Если выбрано "Все категории", сбросить фильтрацию по категориям
        category = None

    if category:
        requests = requests.filter(category=category)

    primary_repair_type = request.GET.get('primary_repair_type')
    secondary_repair_type = request.GET.get('secondary_repair_type')
    last_name = request.GET.get('last_name')
    first_name = request.GET.get('first_name')
    middle_name = request.GET.get('middle_name')
    contact_phone = request.GET.get('contact_phone')
    email = request.GET.get('email')
    street = request.GET.get('street')
    building = request.GET.get('building')
    room = request.GET.get('room')
    status = request.GET.get('status')
    importance = request.GET.get('importance')  # Новый фильтр

    if primary_repair_type:
        requests = requests.filter(primary_repair_type=primary_repair_type)
    if secondary_repair_type:
        requests = requests.filter(secondary_repair_type=secondary_repair_type)
    if last_name:
        requests = requests.filter(last_name__icontains=last_name)
    if first_name:
        requests = requests.filter(first_name__icontains=first_name)
    if middle_name:
        requests = requests.filter(middle_name__icontains=middle_name)
    if contact_phone:
        requests = requests.filter(contact_phone__icontains=contact_phone)
    if email:
        requests = requests.filter(email__icontains=email)
    if street:
        requests = requests.filter(street=street)
    if building:
        requests = requests.filter(building__icontains=building)
    if room:
        requests = requests.filter(room__icontains=room)
    if status:
        requests = requests.filter(status=status)
    if importance:
        requests = requests.filter(importance=importance)
    if assigned_performer:
        if assigned_performer == 'none':
            requests = requests.filter(assigned_performer__isnull=True)
        elif assigned_performer == 'all':
            pass
        else:
            try:
                assigned_performer = int(assigned_performer)
                requests = requests.filter(assigned_performer=assigned_performer)
            except ValueError:
                pass
    elif user.groups.filter(name='Исполнитель').exists() and not assigned_performer:
        requests = requests.filter(assigned_performer=user)

    # Добавляем сортировку
    requests = requests.order_by(
        models.Case(
            models.When(importance='high', then=models.Value(1)),
            models.When(importance='medium', then=models.Value(2)),
            models.When(importance='low', then=models.Value(3)),
            output_field=models.IntegerField(),
        ),
        '-created_at'
    )

    performers = User.objects.filter(groups__name='Исполнитель').exclude(first_name__isnull=True).exclude(
        first_name='').exclude(last_name__isnull=True).exclude(last_name='')

    streets = Street.objects.all()
    form = RequestForm()
    status_choices = Request.STATUS_CHOICES
    importance_choices = Request.IMPORTANCE_CHOICES  # Добавляем важность в контекст

    context = {
        'requests': requests,
        'user': user,
        'is_operator': user.groups.filter(name='Оператор').exists(),
        'is_performer': user.groups.filter(name='Исполнитель').exists(),
        'is_observer': user.groups.filter(name='Наблюдатель').exists(),
        'is_new_user': is_new_user,  # Добавляем флаг нового пользователя
        'performers': performers,
        'streets': streets,
        'form': form,
        'status_choices': status_choices,
        'importance_choices': importance_choices,  # Добавляем важность в контекст
        'performer_default': performer_default if not assigned_performer else assigned_performer,
        'assigned_performer': assigned_performer,
        'use_profile_category': use_profile_category  # передаем в контекст флаг использования категории профиля
    }
    return render(request, 'myapp/dashboard.html', context)


def user_logout(request):
    logout(request)
    return redirect('login')


def request_create(request):
    if request.method == 'POST':
        category = request.POST.get('category', 'small_repair')
        form = RequestForm(request.POST, category=category)
        if form.is_valid():
            request_obj = form.save(commit=False)
            if request.user.is_authenticated:
                request_obj.user = request.user
            request_obj.importance = 'medium'
            request_obj.save()

            middle_name_initial = request_obj.middle_name[0] if request_obj.middle_name else ''

            # Отправка письма при создании заявки
            send_mail(
                subject='Ваша заявка принята на рассмотрение',
                message=f'Уважаемый(ая), {request_obj.last_name} {request_obj.first_name[0]}. {middle_name_initial}.\n'
                        f'Благодарим Вас за обращение в наш сервис и рады сообщить, что Ваша заявка №{request_obj.id} '
                        f'"{request_obj.short_description}" успешно принята и находится на рассмотрении. '
                        f'Мы ценим Ваше терпение и сделаем все возможное, чтобы оперативно решить указанную Вами проблему.\n'
                        f'Если у Вас возникнут дополнительные вопросы или уточнения по заявке, пожалуйста, свяжитесь с нами '
                        f'по электронной почте или телефону, указанному ниже.\n'
                        f'С уважением, Мастерплюс\n'
                        f'masterpluse@masterpluse.ru',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[request_obj.email],
                fail_silently=False,
            )

            messages.success(request, 'Заявка успешно отправлена!')
            return redirect('index')
        else:
            messages.error(request, 'Не все обязательные поля заполнены!')
    else:
        category = request.GET.get('category', 'small_repair')
        form = RequestForm(initial={'category': category}, category=category)
    return render(request, 'myapp/request_form.html', {'form': form})



@login_required
def request_update(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if request.method == 'POST':
        category = request.POST.get('category', 'small_repair')
        form = RequestForm(request.POST, instance=request_obj, category=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заявка успешно обновлена!')
            return redirect('dashboard')
    else:
        category = request.GET.get('category', request_obj.category)
        form = RequestForm(instance=request_obj, category=category)
    return render(request, 'myapp/request_form.html', {'form': form})


@login_required
def request_view(request, pk):
    req = get_object_or_404(Request, pk=pk)
    form = RequestForm(instance=req)
    context = {
        'form': form,
        'request_obj': req,
        'is_read_only': True,
        'is_operator': request.user.groups.filter(name='Оператор').exists() or request.user.is_superuser,
    }
    return render(request, 'myapp/request_view.html', context)

@login_required
def request_delete(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if request.method == 'POST':
        request_obj.delete()
        messages.success(request, 'Заявка успешно удалена!')
        return redirect('dashboard')
    return render(request, 'myapp/request_confirm_delete.html', {'request': request_obj})


@login_required
def profile_edit(request):
    is_operator = request.user.groups.filter(name='Оператор').exists() and not request.user.is_superuser

    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=request.user, user=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Информация профиля успешно обновлена!')
            selected_category = user_form.cleaned_data.get('category')
            return redirect(f'{reverse("dashboard")}?category={selected_category}')
    else:
        user_form = CustomUserChangeForm(instance=request.user, user=request.user)

    if request.user.groups.filter(name='Исполнитель').exists():
        required_fields = ['username', 'first_name', 'last_name', 'email']
        missing_fields = [field for field in required_fields if not getattr(request.user, field)]

        if missing_fields:
            if not any(msg.message == 'Пожалуйста, заполните все обязательные поля перед продолжением работы!' for msg in messages.get_messages(request)):
                messages.error(request, 'Пожалуйста, заполните все обязательные поля перед продолжением работы!')

    return render(request, 'myapp/profile_edit.html', {
        'user_form': user_form,
        'is_operator': is_operator,
    })




@login_required
def change_password(request):
    if request.method == 'POST':
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            old_password = password_form.cleaned_data.get('old_password')
            new_password1 = password_form.cleaned_data.get('new_password1')
            if new_password1 == old_password:
                messages.error(request, 'Новый пароль не должен совпадать с текущим паролем!', extra_tags='error')
            else:
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль успешно изменен!')
                return redirect('login')
        else:
            for field, errors in password_form.errors.items():
                for error in errors:
                    print(f"Error in {field}: {error}")
                    if field == 'new_password2' and 'Пароли не совпадают!' in error:
                        messages.error(request, 'Введенные пароли не совпадают!', extra_tags='error')
                    else:
                        messages.error(request, error, extra_tags='error')
    else:
        password_form = PasswordChangeForm(request.user)
    return render(request, 'myapp/change_password.html', {
        'password_form': password_form,
    })



def ajax_load_repair_types(request):
    category = request.GET.get('category')
    repair_types = RepairType.objects.filter(category=category).order_by('name')
    return render(request, 'myapp/repair_type_dropdown_list_options.html', {'repair_types': repair_types})


def ajax_load_repair_details(request):
    repair_type_id = request.GET.get('repair_type_id')
    repair_details = RepairDetail.objects.filter(repair_type_id=repair_type_id).order_by('name')
    if not repair_details.exists():
        return JsonResponse({'repair_details': []})
    return render(request, 'myapp/repair_detail_dropdown_list_options.html', {'repair_details': repair_details})


@login_required
def request_assign(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if request.method == 'POST':
        performer_id = request.POST.get('performer')
        importance = request.POST.get('importance')

        if performer_id:
            performer = get_object_or_404(User, pk=performer_id)
            request_obj.assigned_performer = performer

        if importance:
            request_obj.importance = importance

        request_obj.save()
        messages.success(request, 'Исполнитель и важность успешно назначены!')
    return redirect('dashboard')


@performer_required
def request_take(request, pk):
    user = request.user
    if not user.first_name or not user.last_name:
        messages.error(request, 'Пожалуйста, заполните поля "Имя" и "Фамилия" перед продолжением работы!')
        return redirect('profile_edit')

    request_obj = get_object_or_404(Request, pk=pk)
    request_obj.status = 'in_progress'
    request_obj.performer = request.user
    request_obj.assigned_performer = request.user  # Set the assigned performer as well
    request_obj.save()

    middle_name_initial = request_obj.middle_name[0] if request_obj.middle_name else ''

    # Отправка письма при взятии заявки в работу
    send_mail(
        subject='Ваша заявка принята в работу',
        message=f'Уважаемый(ая), {request_obj.last_name} {request_obj.first_name[0]}. {middle_name_initial}.\n'
                f'Рады сообщить, что Ваша заявка №{request_obj.id} "{request_obj.short_description}" принята в работу. '
                f'Наши специалисты уже приступили к выполнению Вашей заявки и делают все возможное для скорейшего завершения работ.\n'
                f'Мы будем держать Вас в курсе о ходе выполнения работ и уведомим о завершении. Если у Вас возникнут вопросы или дополнительные уточнения, '
                f'пожалуйста, свяжитесь с нами по электронной почте или телефону, указанному ниже.\n'
                f'С уважением, Мастерплюс\n'
                f'masterpluse@masterpluse.ru',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[request_obj.email],
        fail_silently=False,
    )

    messages.success(request, 'Заявка взята в работу!')
    return redirect('dashboard')

