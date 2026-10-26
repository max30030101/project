from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Max, Min, Q
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CheckoutForm
from .models import Cart, CartItem, Category, Favourite, Order, OrderItem, Product, shipping_for

PER_PAGE = 12
SORTS = [
    ("newest", "Newest first", "-created_at"),
    ("price_asc", "Price: low to high", "sort_price"),
    ("price_desc", "Price: high to low", "-sort_price"),
    ("name", "Name: A to Z", "name"),
]


def _safe_next(request, fallback="shop:list"):
    nxt = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return nxt
    return reverse(fallback)


def _decimal(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


def _active_categories():
    return Category.objects.annotate(n=Count("products", filter=Q(products__is_active=True)))


# ---------------------------------------------------------------- browsing
def home(request):
    products = Product.objects.filter(is_active=True).select_related("category")
    return render(request, "home.html", {
        "featured": products.filter(is_featured=True)[:8],
        "new_arrivals": products.order_by("-created_at")[:4],
        "categories": _active_categories(),
    })


def shop(request, slug=None):
    """Dedicated shop page: search, category + brand + price filters, sorting, pagination.
    Also serves category pages (/shop/category/<slug>/)."""
    category = get_object_or_404(Category, slug=slug) if slug else None
    base = Product.objects.filter(is_active=True).select_related("category")
    if category:
        base = base.filter(category=category)

    qs = base.annotate(sort_price=Coalesce("discount_price", "price"))
    g = request.GET
    q = g.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(brand__icontains=q) | Q(short_description__icontains=q)
                       | Q(description__icontains=q) | Q(category__name__icontains=q))
    selected_categories = [] if category else g.getlist("category")
    if selected_categories:
        qs = qs.filter(category__slug__in=selected_categories)
    selected_brands = g.getlist("brand")
    if selected_brands:
        qs = qs.filter(brand__in=selected_brands)
    min_price, max_price = _decimal(g.get("min_price")), _decimal(g.get("max_price"))
    if min_price is not None:
        qs = qs.filter(sort_price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(sort_price__lte=max_price)
    if g.get("in_stock"):
        qs = qs.filter(stock__gt=0)
    if g.get("on_sale"):
        qs = qs.filter(discount_price__isnull=False)

    sort = g.get("sort", "newest")
    order_by = {key: field for key, _, field in SORTS}.get(sort, "-created_at")
    qs = qs.order_by(order_by, "id")

    page_obj = Paginator(qs, PER_PAGE).get_page(g.get("page"))
    params = g.copy()
    params.pop("page", None)

    bounds = base.annotate(p=Coalesce("discount_price", "price")).aggregate(lo=Min("p"), hi=Max("p"))
    brands = base.exclude(brand="").order_by("brand").values_list("brand", flat=True).distinct()
    return render(request, "shop/shop.html", {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "total": page_obj.paginator.count,
        "active_category": category,
        "categories": _active_categories(),
        "brands": brands,
        "sorts": [(k, label) for k, label, _ in SORTS],
        "sort": sort,
        "q": q,
        "selected_categories": selected_categories,
        "selected_brands": selected_brands,
        "min_price": g.get("min_price", ""),
        "max_price": g.get("max_price", ""),
        "in_stock": bool(g.get("in_stock")),
        "on_sale": bool(g.get("on_sale")),
        "price_bounds": bounds,
        "querystring": params.urlencode(),
        "has_filters": any([q, selected_categories, selected_brands, min_price, max_price, g.get("in_stock"), g.get("on_sale")]),
    })


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    return render(request, "shop/product_detail.html", {"product": product, "related": related})


# -------------------------------------------------------------- favourites
@login_required
def favourites(request):
    items = Favourite.objects.filter(user=request.user, product__is_active=True).select_related("product", "product__category")
    return render(request, "shop/favourites.html", {"items": items})


@require_POST
def favourite_toggle(request, product_id):
    ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if not request.user.is_authenticated:
        login_url = f"{reverse('accounts:login')}?{urlencode({'next': _safe_next(request)})}"
        if ajax:
            return JsonResponse({"login": login_url}, status=401)
        messages.info(request, "Sign in to save favourites.")
        return redirect(login_url)
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    fav, created = Favourite.objects.get_or_create(user=request.user, product=product)
    if not created:
        fav.delete()
    if ajax:
        return JsonResponse({"favourited": created, "count": Favourite.objects.filter(user=request.user).count()})
    messages.success(request, f"{product.name} {'added to' if created else 'removed from'} your favourites.")
    return redirect(_safe_next(request, "shop:favourites"))


# -------------------------------------------------------------------- cart
def _cart_for(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def cart_detail(request):
    items = list(_cart_for(request.user).items.select_related("product", "product__category"))
    subtotal = sum((i.line_total for i in items), Decimal("0"))
    shipping = shipping_for(subtotal)
    return render(request, "shop/cart.html", {
        "items": items, "subtotal": subtotal, "shipping": shipping, "total": subtotal + shipping,
        "has_problem": any(i.quantity > i.product.stock or not i.product.is_active for i in items),
    })


def _qty(request, default=1):
    try:
        return max(1, min(int(request.POST.get("quantity", default)), 99))
    except (TypeError, ValueError):
        return default


@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    if not product.in_stock:
        messages.error(request, f"{product.name} is out of stock right now.")
        return redirect(_safe_next(request))
    item, _ = CartItem.objects.get_or_create(cart=_cart_for(request.user), product=product, defaults={"quantity": 0})
    wanted = item.quantity + _qty(request)
    item.quantity = min(wanted, product.stock)
    item.save()
    if wanted > product.stock:
        messages.warning(request, f"Only {product.stock} of {product.name} in stock — your cart has been set to that.")
    else:
        messages.success(request, f"Added {product.name} to your cart.")
    if request.POST.get("buy_now"):
        return redirect("shop:cart")
    return redirect(_safe_next(request))


@login_required
@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.quantity = min(_qty(request, item.quantity), max(item.product.stock, 1))
    item.save()
    return redirect("shop:cart")


@login_required
@require_POST
def cart_remove(request, item_id):
    get_object_or_404(CartItem, pk=item_id, cart__user=request.user).delete()
    messages.info(request, "Item removed from your cart.")
    return redirect("shop:cart")


# ---------------------------------------------------------------- checkout
@login_required
def checkout(request):
    cart = _cart_for(request.user)
    items = list(cart.items.select_related("product"))
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("shop:cart")
    subtotal = sum((i.line_total for i in items), Decimal("0"))
    shipping = shipping_for(subtotal)

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    locked = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=[i.product_id for i in items])}
                    for i in items:
                        p = locked[i.product_id]
                        if not p.is_active or p.stock < i.quantity:
                            raise ValueError(f"Sorry, only {p.stock} of {p.name} left. Update your cart and try again.")
                    order = form.save(commit=False)
                    order.user = request.user
                    order.subtotal, order.shipping, order.total = subtotal, shipping, subtotal + shipping
                    order.save()
                    for i in items:
                        p = locked[i.product_id]
                        OrderItem.objects.create(order=order, product=p, product_name=p.name,
                                                 unit_price=p.current_price, quantity=i.quantity)
                        p.stock -= i.quantity
                        p.save(update_fields=["stock"])
                    cart.items.all().delete()
            except ValueError as exc:
                messages.error(request, str(exc))
                return redirect("shop:cart")
            return redirect("shop:order_success", order_id=order.pk)
    else:
        u = request.user
        form = CheckoutForm(initial={"full_name": u.get_full_name(), "phone": u.profile.phone, "city": u.profile.city})
    return render(request, "shop/checkout.html", {
        "form": form, "items": items, "subtotal": subtotal, "shipping": shipping, "total": subtotal + shipping,
    })


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, "shop/order_success.html", {"order": order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "shop/orders.html", {"orders": orders})
