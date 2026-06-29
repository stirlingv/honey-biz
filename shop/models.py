from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Product(models.Model):
    """Model for honey products"""
    CATEGORY_CHOICES = [
        ('honey', 'Honey'),
        ('gift', 'Gift & Specialty'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    size = models.CharField(max_length=100, help_text="Jar volume, e.g., Pint, Quart, Gallon")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='honey',
        help_text="'Honey' shows in the main grid; 'Gift & Specialty' shows in the gift jar section",
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'size']

    def __str__(self):
        return f"{self.name} - {self.size}"

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.pk])


class Order(models.Model):
    """Model for honey orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Customer Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    prefer_callback = models.BooleanField(
        default=False,
        help_text="Customer prefers a phone callback"
    )
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)

    # Order Information
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    # Invoice tracking
    invoice_sent_at = models.DateTimeField(blank=True, null=True, help_text="When the QuickBooks invoice was sent to the customer")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"

    def save(self, *args, **kwargs):
        # Calculate total price
        if self.product and self.quantity:
            self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)


class NukeRequest(models.Model):
    """Model for bee starter kit (nuke) purchase requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
    ]

    # Customer Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    prefer_callback = models.BooleanField(
        default=False,
        help_text="Customer prefers a phone callback"
    )
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)

    # Request Information
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of nucs requested"
    )
    experience_level = models.CharField(
        max_length=50,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    preferred_pickup_date = models.DateField(null=True, blank=True)
    notes = models.TextField(
        blank=True,
        help_text="Any additional information or questions"
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Nuc Request'
        verbose_name_plural = 'Nuc Requests'

    def __str__(self):
        return f"Nuc Request #{self.id} - {self.first_name} {self.last_name}"


class PollinationRequest(models.Model):
    """Model for pollination service requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
    ]

    CROP_TYPE_CHOICES = [
        ('citrus', 'Citrus'),
        ('blueberries', 'Blueberries'),
        ('watermelon', 'Watermelon'),
        ('cucumbers', 'Cucumbers'),
        ('squash', 'Squash/Zucchini'),
        ('peppers', 'Peppers'),
        ('tomatoes', 'Tomatoes'),
        ('strawberries', 'Strawberries'),
        ('vegetables', 'Mixed Vegetables'),
        ('orchard', 'Orchard/Fruit Trees'),
        ('other', 'Other'),
    ]

    # Customer Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    prefer_callback = models.BooleanField(
        default=False,
        help_text="Customer prefers a phone callback"
    )

    # Property Information
    property_address = models.TextField(help_text="Address where pollination services are needed")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50, default='FL')
    zip_code = models.CharField(max_length=10)

    # Service Details
    crop_type = models.CharField(max_length=50, choices=CROP_TYPE_CHOICES)
    crop_type_other = models.CharField(max_length=100, blank=True, help_text="If 'Other', please specify")
    acreage = models.DecimalField(max_digits=6, decimal_places=2, help_text="Approximate acreage to be pollinated")
    num_hives_requested = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Number of hives requested (leave blank if unsure, we'll recommend)"
    )
    preferred_start_date = models.DateField(help_text="When do you need the bees?")
    duration_weeks = models.PositiveIntegerField(
        default=4,
        help_text="How many weeks do you need pollination services?"
    )
    notes = models.TextField(blank=True, help_text="Any additional information about your pollination needs")

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    quoted_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pollination Request'
        verbose_name_plural = 'Pollination Requests'

    def __str__(self):
        return f"Pollination Request #{self.id} - {self.first_name} {self.last_name} ({self.crop_type})"


class BeeRemovalRequest(models.Model):
    """Model for bee removal/relocation service requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
    ]

    URGENCY_CHOICES = [
        ('low', 'Low - No immediate concern'),
        ('medium', 'Medium - Would like removed soon'),
        ('high', 'High - Causing problems, need quick response'),
        ('emergency', 'Emergency - Safety concern'),
    ]

    LOCATION_CHOICES = [
        ('tree', 'Tree/Branch'),
        ('wall', 'Inside Wall'),
        ('roof', 'Roof/Eaves'),
        ('ground', 'Ground/Underground'),
        ('shed', 'Shed/Outbuilding'),
        ('fence', 'Fence Post'),
        ('other', 'Other'),
    ]

    PROPERTY_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('agricultural', 'Agricultural/Farm'),
        ('other', 'Other'),
    ]

    # Customer Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    prefer_callback = models.BooleanField(
        default=False,
        help_text="Customer prefers a phone callback"
    )

    # Property Information
    property_address = models.TextField(help_text="Address where bees are located")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50, default='FL')
    zip_code = models.CharField(max_length=10)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='residential')

    # Bee Information
    bee_location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    bee_location_other = models.CharField(max_length=100, blank=True, help_text="If 'Other', please describe")
    how_long_present = models.CharField(
        max_length=100,
        help_text="How long have the bees been there? (e.g., 'Just noticed today', '1 week', 'Several months')"
    )
    estimated_size = models.CharField(
        max_length=100,
        blank=True,
        help_text="Approximate size of the swarm/colony (e.g., 'softball size', 'basketball size', 'large colony')"
    )
    height_from_ground = models.CharField(
        max_length=50,
        blank=True,
        help_text="Approximate height from ground (e.g., '6 feet', '15 feet', 'ground level')"
    )
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='medium')

    # Additional Info
    has_been_sprayed = models.BooleanField(
        default=False,
        help_text="Have the bees been sprayed with pesticides?"
    )
    can_send_photo = models.BooleanField(
        default=False,
        help_text="Are you able to send photos of the bees?"
    )
    notes = models.TextField(blank=True, help_text="Any additional information that might help us")

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    quoted_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    scheduled_date = models.DateTimeField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bee Removal Request'
        verbose_name_plural = 'Bee Removal Requests'

    def __str__(self):
        return f"Bee Removal #{self.id} - {self.first_name} {self.last_name} ({self.urgency})"


class CallbackRequest(models.Model):
    """Model for simple callback requests from the footer"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('completed', 'Completed'),
    ]

    INTEREST_CHOICES = [
        ('honey', 'Honey Products'),
        ('nucs', 'Bee Nucs (Starter Colonies)'),
        ('pollination', 'Pollination Services'),
        ('bee_removal', 'Bee Removal'),
        ('general', 'General Question'),
        ('other', 'Other'),
    ]

    # Contact Information
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, help_text="Optional - for follow-up if we can't reach you by phone")

    # What they're interested in
    interest = models.CharField(
        max_length=20,
        choices=INTEREST_CHOICES,
        default='general',
        help_text="What would you like to discuss?"
    )
    message = models.TextField(
        blank=True,
        help_text="Any additional details (optional)"
    )

    # Best time to call
    best_time = models.CharField(
        max_length=100,
        blank=True,
        help_text="Best time to reach you (optional)"
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Callback Request'
        verbose_name_plural = 'Callback Requests'

    def __str__(self):
        return f"Callback #{self.id} - {self.name} ({self.get_interest_display()})"


class SlackMessage(models.Model):
    """Links a posted Slack notification to the DB record it represents.

    When a notification is posted via the Slack bot API we capture the message
    timestamp (``ts``) and store it here against the order/request. Inbound
    ``reaction_added`` events only carry the channel + ts, so this mapping is
    how we trace a reaction back to the right object to update its status.
    """
    channel = models.CharField(max_length=50)
    ts = models.CharField(max_length=50, help_text="Slack message timestamp")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('channel', 'ts')

    def __str__(self):
        return f"SlackMessage({self.channel}/{self.ts} → {self.target})"

    @classmethod
    def record(cls, channel, ts, obj):
        """Create/refresh the mapping for a posted message."""
        ct = ContentType.objects.get_for_model(obj.__class__)
        return cls.objects.update_or_create(
            channel=channel,
            ts=ts,
            defaults={'content_type': ct, 'object_id': obj.pk},
        )[0]
