from django.contrib import admin
from django.db.models import F

from .models import Cart, CartItem, Category, Favourite, Order, OrderItem, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "position")
    list_editable = ("position",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "price", "discount_price", "stock", "is_active", "is_featured")
    list_editable = ("price", "discount_price", "stock", "is_active", "is_featured")
    list_filter = ("category", "is_active", "is_featured", "brand")
    search_fields = ("name", "brand", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 30
    actions = ["feature", "unfeature", "deactivate"]

    @admin.action(description="Mark selected as featured")
    def feature(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="Remove featured flag")
    def unfeature(self, request, queryset):
        queryset.update(is_featured=False)

    @admin.action(description="Hide selected from the shop")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "city", "total", "payment_method", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "created_at", "state")
    search_fields = ("id", "user__username", "user__email", "full_name", "phone", "pincode")
    readonly_fields = ("user", "subtotal", "shipping", "total", "created_at")
    inlines = [OrderItemInline]
    actions = ["mark_confirmed", "mark_shipped", "mark_delivered", "cancel_and_restock"]

    @admin.action(description="Mark as confirmed")
    def mark_confirmed(self, request, queryset):
        queryset.update(status="confirmed")

    @admin.action(description="Mark as shipped")
    def mark_shipped(self, request, queryset):
        queryset.update(status="shipped")

    @admin.action(description="Mark as delivered")
    def mark_delivered(self, request, queryset):
        queryset.update(status="delivered")

    @admin.action(description="Cancel selected orders and return items to stock")
    def cancel_and_restock(self, request, queryset):
        for order in queryset.exclude(status="cancelled"):
            for item in order.items.all():
                if item.product_id:
                    Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
            order.status = "cancelled"
            order.save(update_fields=["status"])


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    inlines = [CartItemInline]


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_filter = ("created_at",)
