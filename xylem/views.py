from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def index(request):
  return render(request, 'pages/index.html')


def custom_index(request):
	context = {
		"segment": "custom_index"
	}
	if request.user.is_authenticated:
		return redirect("a008:home_schemer")
	return render(request, "pages/custom_index.html", context)


def custom500(request):
	return render(request, "error_pages/500.html")
