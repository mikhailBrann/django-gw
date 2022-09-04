from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models


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


class User(AbstractBaseUser, PermissionsMixin):
    # статусы пользователя
    SUPPLIER = 'supplier'
    BUYER = 'buyer'
    STAFF = 'staff'
    USER_KIND = (
        (SUPPLIER, 'Поставщик'),
        (BUYER, 'Покупатель'),
        (STAFF, 'Сотрудник'),
    )

    full_name = models.CharField(
        max_length=100,
    )
    email = models.EmailField(
        unique=True,
    )
    password = models.CharField(
        max_length=100,
    )
    company = models.CharField(
        max_length=100,
    )
    position = models.CharField(
        max_length=100,
    )
    kind = models.CharField(
        max_length=10,
        choices=USER_KIND,
        blank=False,
    )
    is_active = models.BooleanField(
        default=True,
    )

    USERNAME_FIELD = EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'company', 'position', 'kind']

    objects = UserManager()

    def __str__(self):
        return f'{self.full_name}'

    @property
    def is_supplier(self):
        return self.kind == self.SUPPLIER

    @property
    def is_buyer(self):
        return self.kind == self.BUYER

    @property
    def is_staff(self):
        if self.kind == self.STAFF or self.is_superuser:
            return True
        else:
            return False

    class Meta:
        db_table = 'users'


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
