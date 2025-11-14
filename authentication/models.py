from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()


class Country(models.TextChoices):
    """Country enumeration."""
    AFGHANISTAN = "AF", "Afghanistan"
    ALBANIA = "AL", "Albania"
    ALGERIA = "DZ", "Algeria"
    ARGENTINA = "AR", "Argentina"
    AUSTRALIA = "AU", "Australia"
    AUSTRIA = "AT", "Austria"
    BANGLADESH = "BD", "Bangladesh"
    BELGIUM = "BE", "Belgium"
    BRAZIL = "BR", "Brazil"
    CANADA = "CA", "Canada"
    CHINA = "CN", "China"
    DENMARK = "DK", "Denmark"
    EGYPT = "EG", "Egypt"
    FINLAND = "FI", "Finland"
    FRANCE = "FR", "France"
    GERMANY = "DE", "Germany"
    GREECE = "GR", "Greece"
    INDIA = "IN", "India"
    INDONESIA = "ID", "Indonesia"
    IRELAND = "IE", "Ireland"
    ITALY = "IT", "Italy"
    JAPAN = "JP", "Japan"
    MEXICO = "MX", "Mexico"
    NETHERLANDS = "NL", "Netherlands"
    NEW_ZEALAND = "NZ", "New Zealand"
    NORWAY = "NO", "Norway"
    PAKISTAN = "PK", "Pakistan"
    POLAND = "PL", "Poland"
    PORTUGAL = "PT", "Portugal"
    RUSSIA = "RU", "Russia"
    SAUDI_ARABIA = "SA", "Saudi Arabia"
    SOUTH_AFRICA = "ZA", "South Africa"
    SOUTH_KOREA = "KR", "South Korea"
    SPAIN = "ES", "Spain"
    SWEDEN = "SE", "Sweden"
    SWITZERLAND = "CH", "Switzerland"
    TURKEY = "TR", "Turkey"
    UKRAINE = "UA", "Ukraine"
    UNITED_KINGDOM = "GB", "United Kingdom"
    UNITED_STATES = "US", "United States"
    VIETNAM = "VN", "Vietnam"


class UserProfile(models.Model):
    """Extended user profile with additional personal information."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        help_text="Phone number in international format"
    )
    street = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(
        max_length=2,
        choices=Country.choices,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Profile for {self.user.username}"


# Signal to create profile when user is created
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a profile automatically when a user is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the profile when user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
