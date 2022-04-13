from functools import total_ordering
from django.db import models
from django.dispatch import receiver
from instaloader import PostChangedException

# Create your models here.
class MissGelProducts(models.Model):  
    name = models.CharField(max_length=50)
    color_number = models.CharField(max_length=50)
    packing = models.CharField(max_length=50)
    price = models.FloatField()
    gellifique_name = models.CharField(max_length=50,blank=True,null=True)
    gellifique_old_names = models.CharField(max_length=500,blank=True,null=True)
    gellifique_ean13 = models.CharField(max_length=13,blank=True,null=True)
    gellifique_old_ean13 = models.CharField(max_length=500,blank=True,null=True)
    gellifique_id = models.IntegerField(blank=True,null=True)
    gellifique_old_ids = models.CharField(max_length=500,blank=True,null=True)

    class Meta:
        unique_together = ('name', 'color_number', 'packing',)
        ordering = ['name', 'color_number', 'packing',]

    def __str__(self):
        return self.name + ' ' + self.color_number + ' ' + self.packing

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        self.color_number = self.color_number.upper()
        super().save(*args, **kwargs)

class MissGelOrders(models.Model):  
    class MissGelOrderStatus(models.IntegerChoices):
        DRAFT = 0
        AGREED = 1
        PAID = 2
        SHIPPED = 3
        IN_CUSTOMS = 4
        RECEIVED = 5

    name = models.CharField(max_length=50,unique=True)
    status = models.IntegerField(default=MissGelOrderStatus.DRAFT,choices=MissGelOrderStatus.choices)
    order_dt = models.DateField(blank=True,null=True)
    received_dt = models.DateField(blank=True,null=True)
    batch_code = models.CharField(max_length=50,blank=True,null=True)
    gellifique_code = models.CharField(max_length=50,blank=True,null=True)
    product_cost = models.FloatField(default=0)
    discount = models.FloatField(default=0)
    shipping = models.FloatField(default=0)
    extra_cost1 = models.FloatField(default=0)
    extra_cost2 = models.FloatField(default=0)
    extra_cost3 = models.FloatField(default=0)
    total_cost = models.FloatField(default=0)
    notes = models.TextField(blank=True,null=True)
    doc = models.FileField(upload_to='missgel/%Y/%m/%d/',blank=True,null=True)

    class Meta:
        ordering = ['-name',]

    def __str__(self):
        return self.name

class MissGelOrderDetail(models.Model):  
    order = models.ForeignKey(MissGelOrders,on_delete=models.CASCADE)
    product = models.ForeignKey(MissGelProducts,on_delete=models.CASCADE,blank=True,null=True)
    name = models.CharField(max_length=50)
    color_number = models.CharField(max_length=50)
    packing = models.CharField(max_length=50)
    gellifique_name = models.CharField(max_length=50,blank=True,null=True)
    gellifique_ean13 = models.CharField(max_length=13,blank=True,null=True)
    gellifique_id = models.IntegerField(blank=True,null=True)
    price = models.FloatField(default=0)
    quantity = models.IntegerField(default=0)
    total_cost = models.FloatField(default=0)

    class Meta:
        unique_together = ('order', 'name','color_number','packing',)
        ordering = ['order', 'id',]

    def __str__(self):
        return self.name + ' ' + self.color_number + ' ' + self.packing


