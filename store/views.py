from django.contrib import messages

from django.shortcuts import redirect, render,get_object_or_404

from orders.models import OrderProduct
from .models import Product,ReviewRating
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import ReviewRatingForm

def store(request,category_slug = None):

    categories= None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category,slug = category_slug)
        products = Product.objects.filter(category= categories, is_available = True )
        paginator = Paginator(products,3)
        page = request.GET.get('page')
        paged_products = Paginator.get_page(page)

    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products,3)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)

    context={
        "products": paged_products,
    }

    return render(request,'store/store.html',context)


def product_detail(request,category_slug,product_slug ):
    
    try:    
        single_product = Product.objects.get(category__slug=category_slug,slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id = _cart_id(request),product = single_product).exists()

    except Exception as e:
        raise e

    try:
        if request.user.is_authenticated:
            orderproduct = OrderProduct.objects.filter(user=request.user,product_id= single_product.id).exists()
        else:
            orderproduct=False
    except OrderProduct.DoesNotExist:
         orderproduct:None

    #get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id,status=True)

    context = {
        "single_product":single_product,
        "in_cart":in_cart,
        'orderproduct':orderproduct,
        'reviews':reviews   
    }

    return render(request,'store/product_detail.html',context)


def search(request):
    products = Product.objects.none()
    if "keyword" in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains = keyword) | Q(product_name__icontains = keyword))

    context = {
        "products":products
    }
    return render(request,'store/store.html',context)


def submit_review(request,product_id):

    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":

        try:
            reviews = ReviewRating.objects.get(user__id = request.user.id,product_id = product_id,)
            form = ReviewRatingForm(request.user,instance=reviews)

            form.save()
            messages.success(request, "you review have been successfully updated.")
            return  redirect(url)
        
        except:
            form = ReviewRatingForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.review = form.cleaned_data['review']
                data.rating = form.cleaned_data['rating']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id= product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)