from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    pan = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    financial_year_start = models.CharField(max_length=20, blank=True, null=True)
    currency = models.CharField(max_length=10, default='INR')


class TaxConfiguration(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='tax_configurations')
    gst_rate_0_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_rate_5_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_rate_12_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_rate_18_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_rate_28_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tds_rate_contractor = models.DecimalField(max_digits=5, decimal_places=2, default=0)


class Party(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='parties')
    name = models.CharField(max_length=255)
