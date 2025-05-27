from django.http import HttpResponse

def some_view(request):
    return HttpResponse("This is the some_view response.")