from django.urls import path
from . import views

urlpatterns = [
    path('contacts/', views.contact_list_create, name='contact-list-create'),
    path('contacts/<int:pk>/', views.contact_detail, name='contact-detail'),
    path('contacts/near-destination/', views.contacts_near_destination, name='contacts-near-destination'),
]
