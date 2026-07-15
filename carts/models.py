from django.db import models
from store.models import Product

class Cart(models.Model):
    cart_id =models.CharField(max_length=250,blank=True)
    date_added = models.DateField(auto_now_add=True)


    def __str__(self):
        return self.cart_id

class VariationManager(models.Manager):

    def colors(self):
        return super().filter(variation_category = 'color',is_active=True)
    
    def sizes(self):
        return super().filter(variation_category = 'size',is_active=True)


variation_category_values = (
    ('color' , 'Color'),
    ('size' , 'Size'),
)

class Variation(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100,choices= variation_category_values)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateField(auto_now_add=True)
  
    objects = VariationManager()

    def __str__(self):
        return self.variation_value
    



class CartItem(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)

    variation= models.ManyToManyField(Variation, blank=True)

    cart = models.ForeignKey(Cart,on_delete=models.CASCADE)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)


    def sub_total(self):
        return self.product.price * self.quantity


    def __unicode__(self):
        return str(self.product)




