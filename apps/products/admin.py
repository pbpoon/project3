from django.contrib import admin
from .models import Product, Batch, Category, Quarry


class ProductInline(admin.TabularInline):
    model = Product
    raw_id_fields = ['batch']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    inlines = [ProductInline]


@admin.register(Category)
class CtegoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Quarry)
class QuarryAdmin(admin.ModelAdmin):
    pass
