from django.urls import path

from . import admin_views as adm
from . import seller_views as sel
from . import views

urlpatterns = [
    path("", views.product_list, name="home"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.my_orders, name="my_orders"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("items/<int:pk>/cancel/", views.cancel_item, name="cancel_item"),
    path("items/<int:pk>/return/", views.request_return, name="request_return"),

    path("seller/", sel.dashboard, name="seller_dashboard"),
    path("seller/products/", sel.product_list, name="seller_products"),
    path("seller/products/add/", sel.product_create, name="seller_product_add"),
    path("seller/products/<int:pk>/edit/", sel.product_edit, name="seller_product_edit"),
    path("seller/products/<int:pk>/delete/", sel.product_delete, name="seller_product_delete"),
    path("seller/products/<int:pk>/stock/", sel.stock_update, name="seller_stock"),
    path("seller/orders/", sel.orders, name="seller_orders"),
    path("seller/orders/<int:pk>/advance/", sel.advance_order, name="seller_advance"),
    path("seller/returns/", sel.returns, name="seller_returns"),
    path("seller/returns/<int:pk>/decide/", sel.decide_return, name="seller_return_decide"),

    path("panel/", adm.dashboard, name="admin_dashboard"),
    path("panel/sellers/", adm.sellers, name="admin_sellers"),
    path("panel/sellers/<int:pk>/decision/", adm.seller_decision, name="admin_seller_decision"),
    path("panel/sellers/<int:pk>/commission/", adm.seller_commission, name="admin_seller_commission"),
    path("panel/products/", adm.products, name="admin_products"),
    path("panel/products/<int:pk>/toggle/", adm.product_toggle, name="admin_product_toggle"),
    path("panel/orders/", adm.orders, name="admin_orders"),
    path("panel/commissions/", adm.commissions, name="admin_commissions"),
]
