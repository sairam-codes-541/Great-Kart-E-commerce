from django.urls import path,include
from . import views

urlpatterns = [
    path('place_order',views.place_order,name="place_order"),
    path('payment_success/',views.payment_success,name="payment_success"),
    path('order_complete',views.order_complete,name="order_complete"),
  
]

