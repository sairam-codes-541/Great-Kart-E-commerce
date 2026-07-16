from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from .forms import RegistrationForm
from .models import Account
from django.contrib import messages
from django.http import HttpResponse

#email_verification
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes,force_str
from django.contrib.auth.tokens import default_token_generator



def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(first_name =first_name ,last_name =last_name ,phone_number=phone_number,email=email,password=password,username=username)
            user.phone_number = phone_number
            user.save()

            #verification
            current_site = get_current_site(request)
            mail_subject= "please activate your account"
            message = render_to_string('accounts/account_verification_email.html',{
                'user':user,'domain':current_site,'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()

            #messages.success(request,"Thank you for registering. Please verify your email.")
            return redirect('/accounts/login/?command=verification&email=' + email)





            
    else:

        form = RegistrationForm()

    context ={
        "form": form
    }

    return render(request,'accounts/register.html',context)

def login(request):


    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email,password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request,'Invalid login credentials')
            return redirect('login')
        

    command = request.GET.get('command')
    email = request.GET.get('email')

    context = {
        'command': command,
        'email': email,
    }


    return render(request,'accounts/login.html',context)







@login_required( login_url = login)
def logout(request):

    auth.logout(request)
    messages.error(request,'You are logged out.')
    return redirect('login')
    





def activate(request, uid64, token):

    try:
        uid = force_str(urlsafe_base64_decode(uid64))
        user = Account.objects.get(id=uid)
    
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user,token):

        user.is_active = True
        user.save()

        messages.success(request, "Congratulations! Your account is activated.")
        return redirect("login")

    else: 
        messages.error(request, "Invalid activation link")
        return redirect("register")
    




@login_required(login_url= login)
def dashboard(request):

    return render(request,'accounts/dashboard.html')




def forgotpassword(request):
    if request.method == "POST":
        email = request.POST['email']
        if Account.objects.filter(email=email):
            user = Account.objects.get(email=email)

            current_site = get_current_site(request)
            mail_subject = "Reset your password"
            message = render_to_string('accounts/reset_password_email.html',{
                "user": user,
                "domain":current_site,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user),

            })
            to_email = email
            send_mail = EmailMessage(mail_subject,message, to=[to_email])
            send_mail.send()
            messages.success(request,'Password reset email has been sent your email address')
            return redirect('login')



        else:
            messages.error(request,'Account does not exist')
            return redirect('forgotpassword')



    return render(request,'accounts/forgot_password.html')


def resetpassword_validate(request,uid64, token):
    try: 
        uid = force_str(urlsafe_base64_decode(uid64))
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):

        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('login')
    
def resetPassword(request):
    if request.method == "POST":
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(id=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password has been reset successfully.')
            return redirect('login')

        else:
            messages.error(request, 'Password do not match') 
            return redirect('resetPassword')   


    return render(request,'accounts/resetPassword.html')