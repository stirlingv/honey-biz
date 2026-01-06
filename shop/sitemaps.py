from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Product


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return [
            "home",
            "about",
            "products",
            "order_honey",
            "nuke_request",
            "pollination_services",
            "bee_removal",
            "callback_request",
            "privacy_policy",
            "terms_of_service",
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(in_stock=True)

    def lastmod(self, obj):
        return obj.updated_at
