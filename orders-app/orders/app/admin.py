from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from app.models import User, Contact, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, ConfirmEmailToken


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Управления пользователями
    """
    model = User
    list_display = (
        'first_name',
        'last_name',
        'email',
        'is_staff'
    )
    fieldsets = (
        (None, {
            'fields': ('email', 'password', 'type')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'company', 'position')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        })
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    ...


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    ...


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    ...


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    ...


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    ...


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    ...


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    ...


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    ...


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    ...


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
