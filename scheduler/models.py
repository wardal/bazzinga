from functools import cached_property

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Target(models.Model):
    customer = models.ForeignKey(
        "Customer",
        on_delete=models.CASCADE,
        related_name="targets",
        related_query_name="target",
    )
    email = models.EmailField()

    def __str__(self):
        return f"Target {self.email}"

    def save(self, *args, **kwargs):
        if hasattr(self.customer, "targets_count"):
            del self.customer.targets_count
        super().save(*args, **kwargs)


class Customer(models.Model):
    name = models.CharField(max_length=50)
    interval = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(4)]
    )

    def __str__(self):
        return f"Customer {self.name}"

    @cached_property
    def targets_count(self):
        return self.targets.count()


class Baz(models.Model):
    title = models.CharField(max_length=50)
    content = models.CharField(max_length=50)

    def __str__(self):
        return f"Baz {self.title}"


class CustomerBaz(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="bazes"
    )
    baz = models.ForeignKey(
        Baz, on_delete=models.CASCADE, related_name="customers_bazes"
    )
    finished = models.BooleanField(
        default=False, help_text="Baz was successfully finished"
    )


class BazSendOut(models.Model):
    target = models.ForeignKey(
        Target, on_delete=models.CASCADE, related_name="sent_bazes"
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    baz = models.ForeignKey(Baz, on_delete=models.CASCADE, related_name="sent_bazes")
    datetime = models.DateTimeField()
    interval = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    success = models.BooleanField(default=False)
