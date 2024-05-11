import time
import requests
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.views.generic.base import View
from django.utils.crypto import get_random_string
from django.shortcuts import get_object_or_404,render

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, action, permission_classes

from djoser.views import UserViewSet as DjoserUserViewSet
from djoser.serializers import UsernameSerializer, PasswordSerializer

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from fudhouse.utils import hash_to_smaller_int, base64_encode
from fudhouse.settings import BASE_URL, FRONTEND_URL


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_auth(request):
    return Response({"Message": f"User is authenticated as {request.user.id}, {request.user.username}"})

class CustomUserViewSet(DjoserUserViewSet):
    def get_permissions(self):
        if self.action == 'set_password':
            return []
        else:
            return super().get_permissions()

    # Override the Djoser User delete method to allow deleting without passing current_pasword payload
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

 # Override the Djoser User set password method to allow changing user's password without passing current_pasword payload
    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = PasswordSerializer(data=request.data,  context={'request': request}) # Use only the Password Serializer for validating new password payload
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(id=kwargs['id'])

        user.set_password(serializer.data["new_password"])
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

 # Override the Djoser User set password method to allow changing user's username without passing current_pasword payload
    @action(["post"], detail=False, url_path=f"set_{User.USERNAME_FIELD}")
    def set_username(self, request, *args, **kwargs):
        serializer = UsernameSerializer(data=request.data) # Use only the Username Serializer for validating new username payload
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        new_username = serializer.data["new_" + User.USERNAME_FIELD]

        setattr(user, User.USERNAME_FIELD, new_username)
        user.save()
    
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def user_otp(request):    
    if request.method == 'GET':
        email = request.query_params.get("email")
        user = None

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        
        except User.DoesNotExist:
           return Response({"error": "User with mail address does not exist"}, status=status.HTTP_404_NOT_FOUND)
      
        if 'otp' in request.session:
            del request.session['otp']

        otp = get_random_string(length=4, allowed_chars='0123456789')
  
        request.session['otp'] = {
            'otp': otp,
            'expiry_time': int(time.time()) + 60  # OTP expires after 60 seconds
        }

        send_mail(
            'Your OTP',
            f'Your OTP is: {otp}',
            'lawalmuhammed44@gmail.com',
            [email],
            fail_silently=False,
        )
        return Response({'message': 'OTP sent to user', 'user_id': user.id}, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        if 'otp' not in request.data:
            return Response({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)

        if 'user_id' not in request.data:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'otp' not in request.session:
            return Response({'error': 'OTP session expired'}, status=status.HTTP_400_BAD_REQUEST)

        otp_data = request.session['otp']

        current_time = int(time.time())
        if current_time > otp_data['expiry_time']:
            # OTP has expired
            del request.session['otp']
            return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)

        received_otp = request.data['otp']
        user_id = request.data['user_id']
        stored_otp = otp_data['otp']
        
        if received_otp == stored_otp:
            del request.session['otp']
            return Response({'message': 'OTP verified', 'user_id': user_id}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Incorrect OTP'}, status=status.HTTP_400_BAD_REQUEST)


class ActivateUser(APIView):

    def get(self, request, uid, token):
        payload = {'uid': uid, 'token': token}
        url = f"{BASE_URL}/auth/users/activation/"
        response = requests.post(url, data = payload)
        message = None

        if response.status_code == 204:
            frontend_url = f'{FRONTEND_URL}/account/activate/success'
            return HttpResponseRedirect(frontend_url) 
        elif response.status_code == 400:
            return HttpResponseRedirect(f'{FRONTEND_URL}/account/activate')
        elif response.status_code == 403:
            return HttpResponseRedirect(frontend_url)


class GoogleAuthRedirect(View):
    permission_classes = [AllowAny]
    
    def get(self, request):
        redirect_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY}&response_type=code&scope=https://www.googleapis.com/auth/userinfo.profile%20https://www.googleapis.com/auth/userinfo.email&access_type=offline&redirect_uri={BASE_URL}/api/v1/auth/google/signup"
        return redirect(redirect_url)


class GoogleRedirectURIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Extract the authorization code from the request URL
        code = request.GET.get('code')
        
        if code:
            # Prepare the request parameters to exchange the authorization code for an access token
            token_endpoint = 'https://oauth2.googleapis.com/token'
            token_params = {
                'code': code,
                'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                'redirect_uri': f'{BASE_URL}/api/v1/auth/google/signup',  # Must match the callback URL configured in your Google API credentials
                'grant_type': 'authorization_code',
            }
            
            # Make a POST request to exchange the authorization code for an access token
            response = requests.post(token_endpoint, data=token_params)
            
            if response.status_code == 200:
                access_token = response.json().get('access_token')
                
                if access_token:
                    # Make a request to fetch the user's profile information
                    profile_endpoint = 'https://www.googleapis.com/oauth2/v1/userinfo'
                    headers = {'Authorization': f'Bearer {access_token}'}
                    profile_response = requests.get(profile_endpoint, headers=headers)
                    user = None
                    
                    if profile_response.status_code == 200:
                        data = {}
                        profile_data = profile_response.json()
                        # Proceed with user creation or login

                        uid = hash_to_smaller_int(profile_data['id'])
                      
                        try:
                            user = User.objects.get(id=uid)
                            
                            refresh = RefreshToken.for_user(user)
                            data['access'] = str(refresh.access_token)
                            data['refresh'] = str(refresh)
                            data['user_id'] = str(user.id)
                            return Response(data, status.HTTP_200_OK)

                        except User.DoesNotExist:
                            user = User.objects.create_user(id=uid,fullname=profile_data['name'], username=profile_data['name'],
                                                email=f"{profile_data['email']}-{uid}", password='NIL', is_active=True)
                    
                        refresh = RefreshToken.for_user(user)
                        data['access'] = str(refresh.access_token)
                        data['refresh'] = str(refresh)
                        data['user_id'] = str(user.id)
                        return Response(data, status.HTTP_201_CREATED)
        
        return Response({}, status.HTTP_400_BAD_REQUEST)


class TwitterAuthRedirect(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        redirect_uri = f'{BASE_URL}/api/v1/auth/twitter/signup'  # Callback URL configured in Twitter Developer Dashboard
        auth_url = f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={settings.SOCIAL_AUTH_TWITTER_OAUTH2_KEY}&redirect_uri={redirect_uri}&scope=users.read%20tweet.read%20offline.access&state=state&code_challenge=challenge&code_challenge_method=plain"
        
        return redirect(auth_url)


class TwitterRedirectURIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')

        if code:
            token_url = 'https://api.twitter.com/2/oauth2/token'
            token_params = {
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': f'{BASE_URL}/api/v1/auth/twitter/signup',
                'code_verifier': 'challenge'
            }

            # Client ID and Client Secret obtained from Twitter Developer account
            client_id = settings.SOCIAL_AUTH_TWITTER_OAUTH2_KEY
            client_secret = settings.SOCIAL_AUTH_TWITTER_OAUTH2_SECRET

            # Concatenate client ID and client secret with a colon
            credentials = f"{client_id}:{client_secret}"

            # Encode the concatenated string using Base64
            base64_credentials = base64_encode(credentials)

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {base64_credentials}'
            }

            response = requests.post(token_url, headers=headers, data=token_params)

            if response.status_code == 200:
                access_token = response.json().get('access_token')
                if access_token:
                    user_info_url = 'https://api.twitter.com/2/users/me'
                    headers = {'Authorization': f'Bearer {access_token}'}
                    user_info_response = requests.get(user_info_url, headers=headers)

                    if user_info_response.status_code == 200:
                        data = {}
                        user_info = user_info_response.json()['data']
                        # Proceed with user creation or login
                        
                        uid = user_info['id']
                      
                        try:
                            user = User.objects.get(id=uid)
                            
                            refresh = RefreshToken.for_user(user)
                            data['access'] = str(refresh.access_token)
                            data['refresh'] = str(refresh)
                            data['user_id'] = str(user.id)
                            return Response(data, status.HTTP_200_OK)

                        except User.DoesNotExist:
                            user = User.objects.create_user(id=uid, fullname=user_info['name'], username=user_info['username'],
                                                            email=f"-{uid}", password='Nil', is_active=True)
                    
                        refresh = RefreshToken.for_user(user)
                        data['access'] = str(refresh.access_token)
                        data['refresh'] = str(refresh)
                        data['user_id'] = str(user.id)
                        return Response(data, status.HTTP_201_CREATED)
        
        return Response({}, status.HTTP_400_BAD_REQUEST)