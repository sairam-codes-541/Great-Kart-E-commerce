from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, Payment,OrderProduct
from django.conf import settings
import datetime
import razorpay
from django.views.decorators.http import require_POST
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def place_order(request,total = 0,quantity = 0):
    
    tax = 0
    grand_total = 0

    current_user = request.user
    
    cart_items = CartItem.objects.filter(user=current_user)

    for cart_item in cart_items:
      total += (cart_item.product.price * cart_item.quantity)
      quantity += (cart_item.quantity)
    tax = (2 * total)/100
    grand_total  = tax + total


    cart_count = cart_items.count()
    if cart_count <= 0:
       return redirect('store')

    if request.method == "POST":
      form = OrderForm(request.POST)
      if form.is_valid():
        data = Order()
        data.user = current_user
        data.first_name = form.cleaned_data['first_name']
        data.last_name = form.cleaned_data['last_name']
        data.phone = form.cleaned_data['phone']
        data.email = form.cleaned_data['email']
        data.address_line_1= form.cleaned_data['address_line_1']
        data.address_line_2 = form.cleaned_data['address_line_2']
        data.country = form.cleaned_data['country']
        data.state = form.cleaned_data['state']
        data.city = form.cleaned_data['city']
        data.order_note = form.cleaned_data['order_note']
        data.order_total = grand_total
        data.tax = tax
        data.ip = request.META.get('REMOTE_ADDR')
        data.save()

        #generate order number
        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))

        d = datetime.date(yr, mt, dt)
        current_date = d.strftime("%Y%m%d")
        order_number = current_date + str(data.id)
        data.order_number = order_number
        data.save()

        #create razorpay client
        client = razorpay.Client(
           auth=(
              settings.RAZORPAY_KEY_ID,
              settings.RAZORPAY_KEY_SECRET
           )
        )

        #razorpay uses paise for INR
        razorpay_amount = int(grand_total * 100)

        #Create Razorpay order
        razorpay_order = client.order.create({
           'amount':razorpay_amount,
           'currency':'INR',
           'receipt': order_number,
        })



        order = Order.objects.get(user=current_user,is_ordered=False,order_number=order_number)
        context = {
           
           "cart_items": cart_items,
           "total":total,
           "tax":tax,
           "grand_total":grand_total,
           "order":order,

           #razorpay
           'razorpay_key_id':settings.RAZORPAY_KEY_ID,
           'razorpay_order_id':razorpay_order['id'],
           'razorpay_amount': razorpay_amount,
        }


        return render(request,'orders/payments.html',context)
    else:
       return redirect('checkout')
        




@require_POST
def payment_success(request):
   razorpay_payment_id = request.POST.get('razorpay_payment_id')
   razorpay_order_id = request.POST.get('razorpay_order_id')
   razorpay_signature = request.POST.get('razorpay_signature')
   order_number = request.POST.get('order_number')


   client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,
                                  settings.RAZORPAY_KEY_SECRET))
   

   try:
      #verify razorpay payment signature
      client.utility.verify_payment_signature({
         'razorpay_order_id':razorpay_order_id,
         'razorpay_payment_id': razorpay_payment_id,
         'razorpay_signature': razorpay_signature
      })

      #get our greatkart order
      order = Order.objects.get(
         user=request.user,
         order_number=order_number,
         is_ordered=False
      )


      #create payment object
      payment = Payment.objects.create(
         user=request.user,
         payment_id=razorpay_payment_id,
         payment_method='Razorpay',
         amount_paid=str(order.order_total),
         status='Completed'

      )

      #connect pyment with order
      order.payment = payment
      order.is_ordered = True
      order.save()

      #move the cart items to order product page
      cart_items = CartItem.objects.filter(user=request.user)
      for item in cart_items:
          
         order_product = OrderProduct()
         order_product.order = order
         order_product.payment = payment
         order_product.user = request.user
         order_product.product = item.product
         order_product.quantity = item.quantity
         order_product.product_price = item.product.price
         order_product.ordered= True
         
         order_product.save()

         order_product.variation.set(item.variation.all())
         order_product.save()
   
         # reduce the quantity of the sold products
         product = Product.objects.get(id=item.product_id)
         product.stock -= item.quantity
         product.save()

      #clear the cart
      CartItem.objects.filter(user=request.user).delete()


      #send order recieved email to customer
      mail_subject = 'Thank you for your order!'
      message = render_to_string('orders/order_recieved_email.html',{
         'user': request.user,
         'order': order,
      })
      to_email = request.user.email
      send_email= EmailMessage(mail_subject,message,to=[to_email])
      send_email.send()

      # send order number and transaction id back to senddata method via JsonResponse
      data={
         'order_number': order.order_number,
         'transID': payment.payment_id,
      }

      return redirect(
    f"{reverse('order_complete')}?order_number={order.order_number}&payment_id={payment.payment_id}"
)
   
   except Exception as e:
      print(e)
      return HttpResponse("payment verification",status=400)


def order_complete(request):
   order_number = request.GET.get('order_number')
   payment_id = request.GET.get('payment_id')


   try:

      order= Order.objects.get(order_number=order_number,is_ordered=True)
      payment = Payment.objects.get(payment_id=payment_id)

      ordered_products = OrderProduct.objects.filter(order=order)

      subtotal = sum(item.product_price * item.quantity for item in ordered_products)

      context  = {
         "order":order,
         "payment":payment,
         "ordered_products": ordered_products,
         "subtotal":subtotal,
      }

      return render (request, 'orders/order_complete.html',context)

   except (Order.DoesNotExist, Payment.DoesNotExist):
       return redirect('home')