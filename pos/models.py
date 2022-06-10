from django.db import models
from django.utils.html import mark_safe

# Create your models here.
class Product(models.Model):
    class Meta:
        ordering = ['brand','name']

  
    id_product = models.IntegerField('id',primary_key=True)
    brand  = models.CharField('brand',max_length=50,choices=[('GellifiQue','GellifiQue'),('Siberica','Siberica'),('Staleks','Staleks')],default='GellifiQue')
    reference = models.CharField('reference',max_length=100)
    name  = models.CharField('name',max_length=500)
    price = models.DecimalField('price',max_digits=8, decimal_places=2)
    ean13 = models.TextField('ean13',blank=True,default='')
    quantity = models.IntegerField('quantity',default=0)

    def name_reference(self):
        return mark_safe(self.name+"<br>"+self.reference)

    def ean13_main(self):
        return self.ean13[0:13]

    def barcode_tag(self):
        return mark_safe(f"<svg id='barcode_{self.id_product}'></svg>" +
                "<script>"+
                f"JsBarcode('#barcode_{self.id_product}', '{self.ean13_main()}',"+
                "{height: 60,width: 2,fontSize: 12,font: 'Arial','textMargin':0,'margin':1,'flat':true});"+
                "</script>"
        )

    def sold(self):
        qnt = 0
        prods = OrderDetail.objects.filter(product=self)
        for prod in prods:
            print(prod.order,prod.order.status,prod.quantity)
            if prod.order.status==Order.Status.PAID:
                qnt += prod.quantity

        return qnt



    def __str__(self):
        return self.name + ' -- £'+ str(self.price)

class Order(models.Model):
    customer_name = models.CharField('customer_name',max_length=100,default='-')
    customer_email = models.CharField('customer_email',max_length=100,default='-')
    created_dt = models.DateTimeField('created_dt',auto_now_add=True, null=True)
    updated_dt = models.DateTimeField('created_dt',auto_now=True, null=True)
    subtotal = models.DecimalField('subtotal',max_digits=8, decimal_places=2,default=0)
    #discount_pc = models.IntegerField('discount_pc',default=0)

    class DiscountPc(models.IntegerChoices):
        NONE = 0, '0'
        PC10 = 10, '10%'
        PC20 = 20, '20%'
        PC30 = 30, '30%'
        PC40 = 40, '40%'
        PC50 = 50, '50%'

    discount_pc = models.IntegerField('discount_pc',default=DiscountPc.PC20,choices=DiscountPc.choices)
    discount_gbp = models.DecimalField('discount_gbp',default=0,max_digits=8, decimal_places=2)
    total = models.DecimalField('total',max_digits=8, decimal_places=2,default=0)

    class Status(models.IntegerChoices):
        NEW = 0
        PAID = 1
        CANCELLED = -1
        REFUNDED = -2

    status = models.IntegerField('Status',default=Status.NEW,choices=Status.choices)

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)

        # save original values, when model is loaded from database,
        # in a separate attribute on the model
        instance._loaded_values = dict(zip(field_names, values))

        return instance

    def save(self, *args, **kwargs):
        need_recalc = False
        if not self._state.adding:
            if self.status==Order.Status.PAID and (self._state.adding or self._loaded_values['status']==Order.Status.NEW):
                # do something
                need_recalc = True

        super().save(*args, **kwargs)

class OrderDetail(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='orderdetail_set')
    product = models.ForeignKey(Product,on_delete=models.DO_NOTHING)
    quantity = models.IntegerField('quantity',default=1)



