from django.conf import settings
from django.db.models import Sum

from .models import CartItem, Category, Favourite


def shop_globals(request):
    main, _, accent = settings.SITE_NAME.rpartition(" ")
    if not main:  # one-word name
        main, accent = settings.SITE_NAME, ""
    ctx = {"site_name": settings.SITE_NAME, "brand_main": main, "brand_accent": accent, "nav_categories": Category.objects.all()[:6], "cart_count": 0, "fav_ids": set(), "fav_count": 0}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        ctx["cart_count"] = CartItem.objects.filter(cart__user=user).aggregate(n=Sum("quantity"))["n"] or 0
        ids = set(Favourite.objects.filter(user=user).values_list("product_id", flat=True))
        ctx["fav_ids"] = ids
        ctx["fav_count"] = len(ids)
    return ctx
