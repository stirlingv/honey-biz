from django.apps import AppConfig


class ShopConfig(AppConfig):
    name = 'shop'

    def ready(self):
        from shop import signals
        signals.connect()
