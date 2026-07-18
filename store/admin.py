from django.contrib import admin
from .models import Product,ReviewRating



class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name','price','stock','category','modified_date','is_available',)
    prepopulated_fields = {'slug':('product_name',)}

class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product','user','subject','review','rating','ip','status')

admin.site.register(Product,ProductAdmin)
admin.site.register(ReviewRating,ReviewRatingAdmin)