
from django.urls import path,include
from . import views


urlpatterns = [
    path('register/',views.register,name="register"),
    path('login/',views.login,name="login"),
    path('logout/',views.logout,name='logout'),
    path('forgotpasssword/',views.forgotpassword,name="forgotpassword"),
    path('resetPassword/',views.resetPassword,name="resetPassword"),




    path('activate/<uid64>/<token>/',views.activate,name="activate"),
    path('resetpassword_validate/<uid64>/<token>/',views.resetpassword_validate,name="resetpassword_validate"),



    path('dashboard/', views.dashboard,name="dashboard"),
    path('', views.dashboard,name="dashboard")

    
]



