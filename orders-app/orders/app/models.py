from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django_rest_passwordreset.tokens import get_token_generator

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),

)


# Классы для создания пользователей
class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('нужно указать email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('У суперпользователя значение is_staff равно True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('У суперпользователя значение is_superuser равно True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель пользователей
    """
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = 'email'
    email = models.EmailField(
        'email address',
        unique=True
    )
    company = models.CharField(
        verbose_name='Компания',
        max_length=40,
        blank=True
    )
    position = models.CharField(
        verbose_name='Должность',
        max_length=40,
        blank=True
    )
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        'username',
        max_length=150,
        help_text='150 <= символов. Только буквы, цифры и @/./+/-/_',
        validators=[username_validator],
        error_messages={
            'уникальность': "Пользователь с таким именем уже существует"
        },
    )
    is_active = models.BooleanField(
        'active',
        default=False,
        help_text='Показывает, активен ли пользователь.'
    )
    type = models.CharField(
        verbose_name='Тип пользователя',
        choices=USER_TYPE_CHOICES,
        max_length=5,
        default='buyer'
    )

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)


# 9.
# Contact
# - type
# - user
# - value
class Contact(models.Model):
    phone = models.CharField(max_length=22)
    address = models.CharField(max_length=120)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contacts_user'
    )

    class Meta:
        db_table = 'contacts_user'


# 1.
# Shop
# - name
# - url
# - filename
class Shop(models.Model):
    name = models.CharField(max_length=60, verbose_name='Название магазина')
    url = models.URLField(verbose_name='Ccылка', null=True, blank=True)
    manager = models.OneToOneField(
        User,
        verbose_name='Менеджер',
        related_name='shop',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    working = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'shops'


# 2.
# Category
# - shops(m2m)
# - name
class Category(models.Model):
    name = models.CharField(max_length=120)
    shop = models.ManyToManyField(Shop, related_name='categories')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'categories'


# 3.
# Product
# - category
# - name
class Product(models.Model):
    name = models.CharField(max_length=120)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'products'


# 4.
# ProductInfo
# - product
# - shop
# - name
# - quantity
# - price
# - price_rrc
class ProductInfo(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='detail'
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='product_info'
    )
    suppler_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(verbose_name='Quantity')
    price = models.PositiveIntegerField(verbose_name='Price')
    price_rrc = models.PositiveIntegerField(verbose_name='Recommend Retail Price')
    available = models.BooleanField()

    def __str__(self):
        return self.product.name

    class Meta:
        db_table = 'product_info'
        constraints = [models.UniqueConstraint(
            fields=(
                'product',
                'shop',
                'suppler_id'
            ),
            name='uniq_product'
        )]


# 5.
# Parameter
# - name
class Parameter(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'parameters'


# 6.
# ProductParameter
# - product_info
# - parameter
# - value
class ProductParameter(models.Model):
    value = models.CharField(max_length=120)
    parameter = models.ForeignKey(
        Parameter,
        on_delete=models.CASCADE,
        related_name='product_parameters'
    )
    product_info = models.ForeignKey(
        ProductInfo,
        on_delete=models.CASCADE,
        related_name='parameters'
    )

    def __str__(self):
        return self.value

    class Meta:
        db_table = 'product_parameters'


# 7.
# Order
# - user
# - dt
# - status
class Order(models.Model):
    # состояния заказа
    NEW = 'new'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (NEW, 'Заявка принята'),
        (PROCESSING, 'Заказ обрабатывается'),
        (SHIPPED, 'Заказ отправлен'),
        (DELIVERED, 'Заказ доставлен'),
        (CANCELLED, 'Заказ отменен')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default=NEW
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='order_contact'
    )

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'orders'


# 8.
# OrderItem
# - order
# - product
# - shop
# - quantity
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    product = models.ForeignKey(
        ProductInfo,
        on_delete=models.CASCADE,
        related_name='product_item'
    )
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.product} {self.quantity}'

    class Meta:
        db_table = 'order_items'


class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name="Пользователь, связанный с токеном сброса пароля"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата генерации токен"
    )

    # Key field, though it is not the primary key of the model
    key = models.CharField(
        "Key",
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return f"Токен сброса пароля для пользователя {self.user}"
