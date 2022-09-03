from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator

# состояния
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
    Миксин управления пользователями
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Mетод создает пользователя с именем, email и паролем
        """
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
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель пользователей
    """
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = 'email'
    email = models.EmailField(_('email address'), unique=True)
    company = models.CharField(verbose_name='Компания', max_length=40, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=40, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Обязательно к заполнению. 150 символов или меньше. Только буквы, цифры и @/./+/-/_.'),
        validators=[username_validator],
        error_messages={
            'unique': _("Пользователь с таким именем уже существует."),
        },
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Указывает, следует ли считать этого пользователя активным. '
            'Отмените выбор вместо удаления учетных записей.'
        ),
    )
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)


# 1.
# Shop
# - name
# - url
# - filename
class Shop(models.Model):
    name = models.CharField(max_length=60, verbose_name='Название магазина')
    url = models.URLField(verbose_name='Ccылка', null=True, blank=True)cd
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
        db_name = 'shops'


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
        dbtable = 'products'


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
    pass

    class Meta:
        db_table = 'product_info'
        constants = [models.UniqueConstraint(
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
class Parameter():
    pass



# 6.
# ProductParameter
# - product_info
# - parameter
# - value
class ProductParameter():
    pass


# 7.
# Order
# - user
# - dt
# - status
class Order():
    pass


# 8.
# OrderItem
# - order
# - product
# - shop
# - quantity
class OrderItem():
    pass


# 9.
# Contact
# - type
# - user
# - value
class Contact():
    pass