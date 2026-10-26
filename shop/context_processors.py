from django.db.models import Sum

from .models import CartItem, Category, Favourite


def shop_globals(request):
    ctx = {"nav_categories": Category.objects.all()[:6], "cart_count": 0, "fav_ids": set(), "fav_count": 0}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        ctx["cart_count"] = CartItem.objects.filter(cart__user=user).aggregate(n=Sum("quantity"))["n"] or 0
        ids = set(Favourite.objects.filter(user=user).values_list("product_id", flat=True))
        ctx["fav_ids"] = ids
        ctx["fav_count"] = len(ids)
    return ctx
