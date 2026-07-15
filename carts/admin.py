from django.contrib import admin
from .models import Cart,CartItem,Variation

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product','variation_category','variation_value','is_active')
    list_editable=('is_active',)
    list_filter=('product','variation_category','variation_value',)

class CartItemAdmin(admin.ModelAdmin):
    list_display=('product', 'cart','quantity','is_active')

class CartAdmin(admin.ModelAdmin):
    list_display=('cart_id', 'date_added')


admin.site.register(Cart,CartAdmin)
admin.site.register(CartItem,CartItemAdmin)
admin.site.register(Variation,VariationAdmin)
