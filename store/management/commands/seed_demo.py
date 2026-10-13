from decimal import Decimal

from django.core.management.base import BaseCommand

from accounts.models import SellerProfile, User
from store.models import Category, Order, OrderItem, Product


class Command(BaseCommand):
    help = "Create demo users, categories, products and orders"

    def handle(self, *args, **opts):
        # If demo accounts already exist, refresh image URLs so an existing
        # local database receives the realistic product photography too.
        product_photos = {
            "Wireless Earbuds": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=900&q=85",
            "Smart Watch": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=85",
            "Power Bank 20000mAh": "https://images.unsplash.com/photo-1609592806596-b43badae9f2a?auto=format&fit=crop&w=900&q=85",
            "Mechanical Keyboard": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=85",
            "LED Desk Lamp": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=85",
            "Cotton T-Shirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=85",
            "Denim Jacket": "https://images.unsplash.com/photo-1543076447-215ad9ba6923?auto=format&fit=crop&w=900&q=85",
            "Running Shoes": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85",
            "Leather Wallet": "https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=900&q=85",
            "Ceramic Coffee Mug Set": "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?auto=format&fit=crop&w=900&q=85",
            "Python Programming Basics": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=900&q=85",
            "Data Structures Simplified": "https://images.unsplash.com/photo-1532012197267-da84d127e765?auto=format&fit=crop&w=900&q=85",
        }
        category_photos = {
            "Electronics": "https://images.unsplash.com/photo-1498049794561-7780e7231661?auto=format&fit=crop&w=1000&q=85",
            "Fashion": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1000&q=85",
            "Home & Kitchen": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=1000&q=85",
            "Books": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1000&q=85",
        }
        if User.objects.filter(username="admin").exists():
            for name, url in product_photos.items():
                Product.objects.filter(name=name).update(image_url=url)
            for name, url in category_photos.items():
                Category.objects.filter(name=name).update(image_url=url)
            self.stdout.write(self.style.SUCCESS("Existing demo data found; refreshed product and category photos."))
            return

        User.objects.create_superuser("admin", "admin@example.com", "admin123")

        def seller(username, store, desc, status, rate):
            u = User.objects.create_user(username, f"{username}@example.com", "seller123", role="seller")
            SellerProfile.objects.create(user=u, store_name=store, description=desc, status=status, commission_rate=rate)
            return u

        s1 = seller("seller1", "TechHub", "Gadgets and accessories", "approved", Decimal("10"))
        s2 = seller("seller2", "StyleStreet", "Trendy fashion for everyone", "approved", Decimal("12.5"))
        seller("seller3", "BookNook", "Used and new books", "pending", Decimal("10"))
        c1 = User.objects.create_user("customer1", "c1@example.com", "customer123", role="customer", phone="9876543210")

        cat_data = [("Electronics", "🎧"), ("Fashion", "👕"),
                    ("Home & Kitchen", "🏠"), ("Books", "📚")]
        cats = {n: Category.objects.create(name=n, icon=i, image_url=category_photos[n])
                for n, i in cat_data}
        data = [
            (s1, "Electronics", "Wireless Earbuds", "Bluetooth 5.3 earbuds with 24h battery.", 1499, 25),
            (s1, "Electronics", "Smart Watch", "Fitness tracking, heart-rate and sleep monitor.", 2999, 12),
            (s1, "Electronics", "Power Bank 20000mAh", "Fast-charging, dual USB output.", 1299, 4),
            (s1, "Electronics", "Mechanical Keyboard", "RGB backlit, blue switches.", 2199, 15),
            (s1, "Home & Kitchen", "LED Desk Lamp", "Touch dimmer with 3 colour modes.", 699, 30),
            (s2, "Fashion", "Cotton T-Shirt", "Soft 100% cotton, regular fit.", 499, 50),
            (s2, "Fashion", "Denim Jacket", "Classic blue denim jacket.", 1899, 8),
            (s2, "Fashion", "Running Shoes", "Lightweight breathable shoes.", 2499, 20),
            (s2, "Fashion", "Leather Wallet", "Slim bi-fold wallet.", 799, 3),
            (s2, "Home & Kitchen", "Ceramic Coffee Mug Set", "Set of 4 glossy mugs.", 899, 18),
            (s2, "Books", "Python Programming Basics", "Beginner friendly guide with exercises.", 399, 40),
            (s2, "Books", "Data Structures Simplified", "Visual explanations of core DS.", 549, 22),
        ]
        products = [Product.objects.create(seller=s, category=cats[c], name=n, description=d, price=p, stock=st,
                                           image_url=product_photos[n])
                    for s, c, n, d, p, st in data]

        order = Order.objects.create(customer=c1, full_name="Demo Customer", phone="9876543210",
                                     address="12 Park Street, Kolkata", payment_method="cod")
        total = Decimal("0")
        for prod, qty, status in [(products[0], 1, "delivered"), (products[5], 2, "shipped")]:
            line = prod.price * qty
            rate = prod.seller.seller_profile.commission_rate
            OrderItem.objects.create(order=order, product=prod, seller=prod.seller, product_name=prod.name,
                                     price=prod.price, quantity=qty, commission_rate=rate,
                                     commission_amount=(line * rate / 100).quantize(Decimal("0.01")), status=status)
            prod.stock -= qty
            prod.save()
            total += line
        order.total = total
        order.save()
        self.stdout.write(self.style.SUCCESS("Demo data created: admin/admin123, seller1/seller123, seller2/seller123, customer1/customer123"))
