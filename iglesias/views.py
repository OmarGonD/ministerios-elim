from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import IglesiaForm
from .models import Iglesia
from django.core.paginator import Paginator


@login_required
def my_iglesias(request):
    items = Iglesia.objects.filter(owner=request.user)
    return render(request, 'iglesias/my_iglesias.html', {'iglesias': items})


def iglesias_index(request):
    """Public list of all iglesias with optional country filter."""
    qs = Iglesia.objects.all().order_by('-created')
    country = request.GET.get('country')
    if country:
        qs = qs.filter(country__iexact=country)
    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # list of distinct countries for the filter dropdown
    countries = Iglesia.objects.values_list('country', flat=True).distinct().exclude(country='')
    return render(request, 'iglesias/list.html', {'page_obj': page_obj, 'countries': countries, 'selected_country': country})


@login_required
def create_iglesia(request):
    if request.method == 'POST':
        form = IglesiaForm(request.POST, request.FILES)
        if form.is_valid():
            iglesia = form.save(commit=False)
            iglesia.owner = request.user
            iglesia.save()
            return redirect('iglesias:iglesia_detail', pk=iglesia.pk)
    else:
        form = IglesiaForm()
    return render(request, 'iglesias/create_iglesia.html', {'form': form})


@login_required
def edit_iglesia(request, pk):
    iglesia = get_object_or_404(Iglesia, pk=pk)
    if iglesia.owner != request.user and not request.user.is_staff:
        return redirect('iglesias:my_iglesias')
    if request.method == 'POST':
        form = IglesiaForm(request.POST, request.FILES, instance=iglesia)
        if form.is_valid():
            form.save()
            return redirect('iglesias:iglesia_detail', pk=iglesia.pk)
    else:
        form = IglesiaForm(instance=iglesia)
    return render(request, 'iglesias/edit_iglesia.html', {'form': form, 'iglesia': iglesia})


def iglesia_detail(request, pk):
    """Public detail view of an iglesia."""
    iglesia = get_object_or_404(Iglesia, pk=pk)
    
    # Check if user can edit this iglesia
    can_edit = False
    if request.user.is_authenticated:
        can_edit = (iglesia.owner == request.user) or request.user.is_staff
    
    return render(request, 'iglesias/detail.html', {
        'iglesia': iglesia,
        'can_edit': can_edit
    })
