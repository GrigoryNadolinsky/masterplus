from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
class Street(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class RepairType(models.Model):
    CATEGORY_CHOICES = [
        ('small_repair', 'Мелкий ремонт'),
        ('sub_work', 'Подсобные работы'),
        ('warehouse', 'Склад'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class RepairDetail(models.Model):
    repair_type = models.ForeignKey(RepairType, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Request(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершено'),
        ('closed', 'Закрыто'),
    ]

    CATEGORY_CHOICES = [
        ('small_repair', 'Мелкий ремонт'),
        ('sub_work', 'Подсобные работы'),
        ('warehouse', 'Склад'),
    ]
    IMPORTANCE_CHOICES = [
        ('low', 'Низкая'),
        ('medium', 'Средняя'),
        ('high', 'Высокая'),
    ]
    importance = models.CharField(max_length=10, choices=IMPORTANCE_CHOICES, default='medium')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='small_repair')
    primary_repair_type = models.ForeignKey(RepairType, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_requests')
    secondary_repair_type = models.ForeignKey(RepairDetail, on_delete=models.SET_NULL, null=True, blank=True, related_name='secondary_requests')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True, null=True)
    short_description = models.CharField(max_length=100)
    street = models.ForeignKey(Street, on_delete=models.CASCADE, null=True, blank=True)
    building = models.CharField(max_length=10, null=True, blank=True)
    room = models.CharField(max_length=10, null=True, blank=True)
    contact_phone = models.CharField(max_length=20)
    email = models.EmailField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_performer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    performer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_requests')

    def __str__(self):
        return f'{self.last_name} {self.first_name} - {self.category}'


class User(AbstractUser):
    CATEGORY_CHOICES = [
        ('small_repair', 'Мелкий ремонт'),
        ('sub_work', 'Подсобные работы'),
        ('warehouse', 'Склад'),
    ]

    middle_name = models.CharField(max_length=30, blank=True, null=True, verbose_name='Отчество')
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Номер телефона')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True, verbose_name='Категория')
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class AdminLog(models.Model):
    action_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField(blank=True)

    class Meta:
        verbose_name = _("log entry")
        verbose_name_plural = _("log entries")

    def __str__(self):
        return self.object_repr

    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("Дата создания"))