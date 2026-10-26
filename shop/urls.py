from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("shop/", views.shop, name="list"),
    path("shop/category/<slug:slug>/", views.shop, name="category"),
    path("product/<slug:slug>/", views.product_detail, name="detail"),
    path("favourites/", views.favourites, name="favourites"),
    path("favourites/toggle/<int:product_id>/", views.favourite_toggle, name="favourite_toggle"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:item_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:item_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_list, name="orders"),
    path("orders/<int:order_id>/confirmed/", views.order_success, name="order_success"),
]
