from decimal import Decimal

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def unique_slug(instance, source, field="slug"):
    base = slugify(source) or "item"
    slug, n = base, 2
    Model = instance.__class__
    while Model.objects.filter(**{field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    position = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers appear first.")

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:category", args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    brand = models.CharField(max_length=80, blank=True)
    short_description = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField("MRP (₹)", max_digits=10, decimal_places=2)
    discount_price = models.DecimalField("Sale price (₹)", max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, help_text="Untick to hide from the shop.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_active", "category"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:detail", args=[self.slug])

    @property
    def current_price(self):
        if self.discount_price is not None and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def on_sale(self):
        return self.current_price < self.price

    @property
    def discount_percent(self):
        if self.on_sale:
            return int(round((self.price - self.current_price) / self.price * 100))
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def low_stock(self):
        return 0 < self.stock <= 5


class Favourite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favourites")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="favourited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ♥ {self.product}"


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user}"

    @property
    def subtotal(self):
        return sum((i.line_total for i in self.items.select_related("product")), Decimal("0"))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} × {self.product}"

    @property
    def line_total(self):
        return self.product.current_price * self.quantity


def shipping_for(subtotal):
    if subtotal <= 0 or subtotal >= settings.FREE_SHIPPING_THRESHOLD:
        return Decimal("0")
    return Decimal(settings.SHIPPING_FEE)


class Order(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    PAYMENT = [("cod", "Cash on delivery")]  # online payments are a planned enhancement

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=15, validators=[RegexValidator(r"^[0-9+\- ]{10,15}$", "Enter a valid phone number.")])
    address_line = models.CharField("Address", max_length=255)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    pincode = models.CharField(max_length=6, validators=[RegexValidator(r"^[1-9][0-9]{5}$", "Enter a valid 6-digit PIN code.")])
    payment_method = models.CharField(max_length=10, choices=PAYMENT, default="cod")
    status = models.CharField(max_length=12, choices=STATUS, default="pending")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=160)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
