from datetime import datetime as dt

from django.shortcuts import render
from rest_framework.views import APIView
# from rest_framework.response import Response
from django.http.response import HttpResponse

# Create your views here.


class MessageViewSet(APIView):
    def get(self, request):
        return HttpResponse(f'Bom dia! {dt.today()}')
