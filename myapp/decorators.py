# myapp/decorators.py
from django.contrib.auth.decorators import user_passes_test

def is_superuser(user):
    return user.is_superuser

def is_operator(user):
    return user.groups.filter(name='Оператор').exists()

def is_performer(user):
    return user.groups.filter(name='Исполнитель').exists()

def is_observer(user):
    return user.groups.filter(name='Наблюдатель').exists()

def admin_required(view_func):
    return user_passes_test(is_superuser)(view_func)

def operator_required(view_func):
    return user_passes_test(is_operator)(view_func)

def performer_required(view_func):
    return user_passes_test(is_performer)(view_func)

def observer_required(view_func):
    return user_passes_test(is_observer)(view_func)

