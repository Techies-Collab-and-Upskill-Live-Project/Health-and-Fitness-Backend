from django.urls import path, include

from rest_framework.urlpatterns import format_suffix_patterns

from .views import user_otp, CustomUserViewSet, GoogleAuthRedirect, GoogleRedirectURIView, TwitterAuthRedirect, TwitterRedirectURIView,test_auth

urlpatterns = [
    path('auth/users/otp/', user_otp, name="user-otp"),
    path('auth/users/<int:id>/delete/', CustomUserViewSet.as_view({'delete': 'destroy'}), name='user-delete'),
    path('auth/users/<int:id>/set_password/', CustomUserViewSet.as_view({'post': 'set_password'}), name='user-set-password'),
    path('auth/users/set_username/', CustomUserViewSet.as_view({'post': 'set_username'}), name='user-set-username'),
    path("auth/google-signup/", GoogleAuthRedirect.as_view(), name="google-redirect-user"),
    path("auth/google/signup/", GoogleRedirectURIView.as_view(), name="google-handle-redirect"),   
    path("auth/twitter-signup/", TwitterAuthRedirect.as_view(), name="twitter-redirect-user"),
    path("auth/twitter/signup/", TwitterRedirectURIView.as_view(), name="twitter-handle-redirect"),   
    path("test-auth/", test_auth), 
]