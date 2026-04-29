from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from django.db.models import Q
from urllib.parse import quote

from .forms import BlogForm, ContactForm, TestimonialForm, ActivityForm, CampingPackageForm, BookingForm
from .models import Blog, Category, ContactMessage, GalleryImage, Testimonial, Activity, CampingPackage, Booking

def home(request):
    testimonials = Testimonial.objects.all().order_by("-created_at")[:5]
    camping_packages = CampingPackage.objects.all().order_by("-created_at")[:6]
    activities = Activity.objects.all().order_by("-created_at")[:6]
    blogs = Blog.objects.all().order_by("-created_at")[:3]
    return render(request, 'frontend/index.html', {
        'testimonials': testimonials,
        'camping_packages': camping_packages,
        'activities': activities,
        'blogs': blogs
    })

def about(request):
    testimonials = Testimonial.objects.all().order_by("-created_at")[:5]
    camping_packages = CampingPackage.objects.all().order_by("-created_at")[:6]
    return render(request, 'frontend/about.html', {
        'testimonials': testimonials,
        'camping_packages': camping_packages
    })

def services(request):
    return render(request, 'frontend/services.html')

def services_details(request):
    return render(request, 'frontend/services-details.html')

def activities(request):
    activities_qs = Activity.objects.all().order_by('-created_at')
    paginator = Paginator(activities_qs, 6) # Show 6 activities per page
    page_number = request.GET.get("page")
    activities_list = paginator.get_page(page_number)
    testimonials = Testimonial.objects.all().order_by("-created_at")[:5]
    return render(request, 'frontend/activities.html', {'activities': activities_list, 'testimonials': testimonials})

def activity_details(request, slug):
    activity = get_object_or_404(Activity, slug=slug)
    return render(request, 'frontend/activity-details.html', {'activity': activity})

def blog_grid(request):
    blogs_qs = Blog.objects.all().order_by("-created_at")
    paginator = Paginator(blogs_qs, 9)
    page_number = request.GET.get("page")
    blogs = paginator.get_page(page_number)
    testimonials = Testimonial.objects.all().order_by("-created_at")[:3]
    return render(request, "frontend/blog-grid.html", {"blogs": blogs, "testimonials": testimonials})

def blog_standard(request):
    return render(request, 'frontend/blog-standard.html')

def gallery(request):
    categories = Category.objects.all()
    gallery_images = GalleryImage.objects.select_related('category').all().order_by('-uploaded_at')
    return render(request, 'frontend/gallery.html', {
        'categories': categories,
        'gallery_images': gallery_images
    })

def blog_details(request, slug=None):
    if slug:
        blog = get_object_or_404(Blog, slug=slug)
    else:
        blog = Blog.objects.order_by("-created_at").first()
        if not blog:
            return redirect("blog_grid")
    recent_blogs = Blog.objects.exclude(id=blog.id).order_by("-created_at")[:4]
    testimonials = Testimonial.objects.all().order_by("-created_at")[:3]
    gallery_images = GalleryImage.objects.all().order_by('-uploaded_at')[:6]
    return render(
        request,
        "frontend/blog-details.html",
        {"blog": blog, "recent_blogs": recent_blogs, "testimonials": testimonials, "gallery_images": gallery_images},
    )

def camping(request):
    return render(request, 'frontend/camping.html')

def camping_details(request, slug=None):
    if slug:
        package = get_object_or_404(CampingPackage, slug=slug)
    else:
        # Fallback for old URL if needed, or just redirect
        package = CampingPackage.objects.first()
    
    return render(request, 'frontend/camping-details.html', {'package': package})

def camping_donation(request):
    return render(request, 'frontend/camping-donation.html')

def donations(request):
    return render(request, 'frontend/donations.html')

def contact(request):
    if request.method == "POST":
        full_name = (request.POST.get("name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()
        user_message = (request.POST.get("message") or "").strip()

        location = (request.POST.get("location") or "").strip()
        contact_time = (request.POST.get("contact_time") or "").strip()

        if not full_name or not phone:
            messages.error(request, "Please enter your name and phone number.")
            return render(
                request,
                "frontend/contact.html",
                {"contact_form_data": request.POST},
            )

        name_parts = full_name.split(None, 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        final_message = user_message

        ContactMessage.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email or None,
            message=final_message,
            best_time_to_contact=contact_time or None,
        )
        messages.success(request, "Your message has been sent successfully. We will contact you soon.")
        return redirect("contact")

    return render(request, 'frontend/contact.html')

def volunteer(request):
    return render(request, 'frontend/volunteer.html')

def volunteer_details(request):
    return render(request, 'frontend/volunteer-details.html')

def be_volunteer(request):
    return render(request, 'frontend/be-volunteer.html')

def page_not_found(request, exception):
    return render(request, 'frontend/404.html', status=404)


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "Both fields are required.")
            return render(request, "authenticate/login.html")

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("admin_dashboard")

        messages.error(request, "Invalid credentials or unauthorized access.")

    return render(request, "authenticate/login.html")


@login_required(login_url="admin_login")
def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("admin_login")


import datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta

@login_required(login_url="admin_login")
def admin_dashboard(request):
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Total Stats
    stats = {
        'total_blogs': Blog.objects.count(),
        'blogs_this_month': Blog.objects.filter(created_at__gte=month_start).count(),
        'total_services': Category.objects.count(),
        'total_contacts': ContactMessage.objects.count(),
        'total_packages': CampingPackage.objects.count(),
        'total_activities': Activity.objects.count()
    }

    # 2. Recent Lists
    recent_blogs = Blog.objects.all().order_by('-created_at')[:4]
    recent_contacts = ContactMessage.objects.all().order_by('-created_at')[:4]
    recent_packages = CampingPackage.objects.all().order_by('-created_at')[:4]
    recent_activities = Activity.objects.all().order_by('-created_at')[:4]

    # 3. Chart Data (Blogs vs Contacts over last 6 months)
    month_labels = []
    blogs_counts = []
    contacts_counts = []
    
    for i in range(5, -1, -1):
        target_month = now - relativedelta(months=i)
        label = target_month.strftime('%b')
        month_labels.append(label)
        
        blogs_count = Blog.objects.filter(
            created_at__year=target_month.year,
            created_at__month=target_month.month
        ).count()
        blogs_counts.append(blogs_count)
        
        contacts_count = ContactMessage.objects.filter(
            created_at__year=target_month.year,
            created_at__month=target_month.month
        ).count()
        contacts_counts.append(contacts_count)
        
    # 4. Service Distribution (Doughnut Chart)
    service_labels = []
    service_counts = []
    for category in Category.objects.all()[:6]: # Limit to top 6 categories for visual fit
        service_labels.append(category.name)
        # Using GalleryImage count as a proxy for category size since there is no direct service linkage
        service_counts.append(category.images.count())
        
    if not service_labels: # Fallback if empty to load chart cleanly
        service_labels = ['No Data']
        service_counts = [1]

    context = {
        'stats': stats,
        'recent_blogs': recent_blogs,
        'recent_contacts': recent_contacts,
        'recent_packages': recent_packages,
        'recent_activities': recent_activities,
        'month_labels': month_labels,
        'blogs_counts': blogs_counts,
        'contacts_counts': contacts_counts,
        'service_labels': service_labels,
        'service_counts': service_counts,
    }

    return render(request, "admin_pages/dashboard.html", context)



# ==========================================
# 6. BLOGS (ADMIN)
# ==========================================

@login_required(login_url="admin_login")
def admin_blog_list(request):  # RENAMED from blog_list to fix URL error
    blogs_qs = Blog.objects.all().order_by("-created_at")
    paginator = Paginator(blogs_qs, 6)
    page_number = request.GET.get("page")
    blogs = paginator.get_page(page_number)

    return render(request, "admin_pages/blog_list.html", {"blogs": blogs})

@login_required(login_url="admin_login")
def blog_create(request):
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Blog post created!")
            return redirect("admin_blog_list")
    else:
        form = BlogForm()
    return render(request, "admin_pages/create_blog.html", {"form": form})

@login_required(login_url="admin_login")
def blog_update(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, "Blog updated!")
            return redirect("admin_blog_list")
    else:
        form = BlogForm(instance=blog)
    return render(request, "admin_pages/create_blog.html", {"form": form, "blog": blog})

@login_required(login_url="admin_login")
def blog_delete(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    if request.method == "POST":
        blog.delete()
        messages.success(request, "Blog deleted.")
    return redirect("admin_blog_list")


# ==========================================
# 7. GALLERY (ADMIN)
# ==========================================

@login_required(login_url="admin_login")
def gallery_images(request):
    categories = Category.objects.all().prefetch_related("images")
    category_pages = {}
    for category in categories:
        images_qs = category.images.all().order_by("-uploaded_at")
        paginator = Paginator(images_qs, 8)
        page_number = request.GET.get(f"page_{category.id}", 1)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        category_pages[category.id] = page_obj

    return render(
        request, "admin_pages/image_list.html",
        {"categories": categories, "category_pages": category_pages},
    )

@login_required(login_url="admin_login")
def add_image(request):
    categories = Category.objects.all()
    if request.method == "POST":
        category_id = request.POST.get("category")
        category = Category.objects.get(id=category_id)
        files = request.FILES.getlist("images")
        for file in files:
            GalleryImage.objects.create(
                category=category,
                title=file.name,
                image=file,
            )
        messages.success(request, "Images uploaded successfully!")
        return redirect("list_image")

    return render(request, "admin_pages/add_image.html", {"categories": categories})

@login_required(login_url="admin_login")
def delete_image(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    if request.method == "POST":
        image.delete()
        messages.success(request, "Image deleted successfully!")
        return redirect("list_image")
    return render(request, "admin_pages/image_list.html", {"image": image})


@login_required(login_url="admin_login")
def category_list(request):
    categories = Category.objects.all().order_by("-created_at")
    paginator = Paginator(categories, 10)
    page_number = request.GET.get("page")
    categories = paginator.get_page(page_number)
    return render(request, "admin_pages/category_list.html", {"categories": categories})


@login_required(login_url="admin_login")
def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Category.objects.create(name=name)
            messages.success(request, "Category created successfully!")
            return redirect("category_list")
    return render(request, "admin_pages/add_category.html")


@login_required(login_url="admin_login")
def update_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.name = request.POST.get("name")
        category.save()
        messages.success(request, "Category updated successfully!")
        return redirect("category_list")
    return redirect("category_list")


@login_required(login_url="admin_login")
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully!")
        return redirect("category_list")
    return redirect("category_list")


# ==========================================
# 8. TESTIMONIALS (ADMIN)
# ==========================================

@login_required(login_url="admin_login")
def testimonial_list(request):
    testimonials_list = Testimonial.objects.all().order_by(Lower("name"))
    paginator = Paginator(testimonials_list, 6)
    page_number = request.GET.get("page")
    testimonials = paginator.get_page(page_number)
    return render(request, "admin_pages/review_list.html", {"testimonials": testimonials})


@login_required(login_url="admin_login")
def testimonial_create(request):
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Testimonial added successfully!")
            return redirect("review_list")
    else:
        form = TestimonialForm()
    return render(request, "admin_pages/create_review.html", {"form": form})


@login_required(login_url="admin_login")
def testimonial_update(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES, instance=testimonial)
        if form.is_valid():
            form.save()
            messages.success(request, "Testimonial updated successfully!")
            return redirect("review_list")
    else:
        form = TestimonialForm(instance=testimonial)
    return render(request, "admin_pages/review_list.html", {"form": form, "testimonial": testimonial})


@login_required(login_url="admin_login")
def testimonial_delete(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if request.method == "POST":
        testimonial.delete()
        messages.success(request, "Testimonial deleted successfully!")
        return redirect("review_list")
    return render(request, "admin_pages/review_list.html", {"testimonial": testimonial})


# ==========================================
# 9. CONTACTS & INQUIRIES (ADMIN)
# ==========================================

@login_required(login_url="admin_login")
def view_contacts(request):
    ContactMessage.objects.filter(is_read=False).update(is_read=True)
    contacts = ContactMessage.objects.all().order_by("-created_at")
    paginator = Paginator(contacts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "admin_pages/view_contacts.html", {"contacts": page_obj})

@login_required(login_url="admin_login")
def delete_contact(request, pk):
    contact = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        contact.delete()
    return redirect("view_contacts")


# ==========================================
# 9.5 BOOKINGS (FRONTEND AND ADMIN)
# ==========================================

def booking(request):
    packages = CampingPackage.objects.all()
    form = BookingForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Booking request sent successfully. We will contact you soon.")
            return redirect("booking")
        messages.error(request, "Please check the form and try again.")
    return render(request, "frontend/booking.html", {
        "form": form,
        "packages": packages,
    })

@login_required(login_url="admin_login")
def admin_view_bookings(request):
    Booking.objects.filter(is_read=False).update(is_read=True)
    bookings = Booking.objects.all().order_by("-created_at")
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "admin_pages/view_bookings.html", {"bookings": page_obj})

@login_required(login_url="admin_login")
def admin_delete_booking(request, pk):
    booking_obj = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        booking_obj.delete()
        messages.success(request, "Booking deleted successfully!")
    return redirect("admin_view_bookings")


# ==========================================
# 10. ACTIVITIES (FRONTEND)
# ==========================================

def activity_list(request):
    # Fetch activities, ordered by newest first
    activities_qs = Activity.objects.all().order_by("-created_at")
    paginator = Paginator(activities_qs, 9)
    page_number = request.GET.get("page")
    activities = paginator.get_page(page_number)
    testimonials = list(Testimonial.objects.all()[:8])
    if testimonials and len(testimonials) < 3:
        repeat_count = (3 + len(testimonials) - 1) // len(testimonials)
        testimonials = (testimonials * repeat_count)[:3]
    return render(request, "frontend/activities.html", {"activities": activities, "testimonials": testimonials})


def activity_single(request, slug):
    activity = get_object_or_404(Activity, slug=slug)
    # Optional: fetch other recent activities for a sidebar
    recent_activities = Activity.objects.exclude(slug=slug)[:3]
    context = {"activity": activity, "recent_activities": recent_activities}
    return render(request, "frontend/activity-single.html", context)


# ==========================================
# 11. ACTIVITIES (ADMIN DASHBOARD)
# ==========================================

@login_required(login_url="admin_login")
def admin_activity_list(request):
    activities_qs = Activity.objects.all().order_by("-created_at")
    paginator = Paginator(activities_qs, 10)
    page_number = request.GET.get("page")
    activities = paginator.get_page(page_number)
    return render(request, "admin_pages/activity_list.html", {"activities": activities})


@login_required(login_url="admin_login")
def activity_create(request):
    if request.method == "POST":
        form = ActivityForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Activity created successfully!")
            return redirect("admin_activity_list")
    else:
        form = ActivityForm()
    return render(request, "admin_pages/create_activity.html", {"form": form})


@login_required(login_url="admin_login")
def activity_update(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    if request.method == "POST":
        form = ActivityForm(request.POST, request.FILES, instance=activity)
        if form.is_valid():
            form.save()
            messages.success(request, "Activity updated successfully!")
            return redirect("admin_activity_list")
    else:
        form = ActivityForm(instance=activity)
    # Reusing the create template for editing is common practice
    return render(request, "admin_pages/create_activity.html", {"form": form, "activity": activity})


@login_required(login_url="admin_login")
def activity_delete(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    if request.method == "POST":
        activity.delete()
        messages.success(request, "Activity deleted successfully!")
    return redirect("admin_activity_list")


# ==========================================
# 12. CAMPING PACKAGES (FRONTEND)
# ==========================================

def services(request):
    packages_qs = CampingPackage.objects.all().order_by("-created_at")
    paginator = Paginator(packages_qs, 9)
    page_number = request.GET.get("page")
    packages = paginator.get_page(page_number)
    activities = Activity.objects.all()[:4]
    return render(request, "frontend/services.html", {"packages": packages, "activities": activities})


def service_single(request, slug):
    package = get_object_or_404(CampingPackage, slug=slug)
    recent_packages = CampingPackage.objects.exclude(slug=slug).order_by("-created_at")[:5]
    return render(request, "frontend/service-single.html", {"package": package, "recent_packages": recent_packages})


# ==========================================
# 13. CAMPING PACKAGES (ADMIN DASHBOARD)
# ==========================================

@login_required(login_url="admin_login")
def admin_camping_package_list(request):
    packages_qs = CampingPackage.objects.all().order_by("-created_at")
    paginator = Paginator(packages_qs, 10)
    page_number = request.GET.get("page")
    packages = paginator.get_page(page_number)
    return render(request, "admin_pages/camping_package_list.html", {"packages": packages})


@login_required(login_url="admin_login")
def camping_package_create(request):
    if request.method == "POST":
        form = CampingPackageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Camping Package created successfully!")
            return redirect("admin_camping_package_list")
    else:
        form = CampingPackageForm()
    return render(request, "admin_pages/create_camping_package.html", {"form": form})


@login_required(login_url="admin_login")
def camping_package_update(request, pk):
    package = get_object_or_404(CampingPackage, pk=pk)
    if request.method == "POST":
        form = CampingPackageForm(request.POST, request.FILES, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, "Camping Package updated successfully!")
            return redirect("admin_camping_package_list")
    else:
        form = CampingPackageForm(instance=package)
    return render(request, "admin_pages/create_camping_package.html", {"form": form, "package": package})


@login_required(login_url="admin_login")
def camping_package_delete(request, pk):
    package = get_object_or_404(CampingPackage, pk=pk)
    if request.method == "POST":
        package.delete()
        messages.success(request, "Camping Package deleted successfully!")
    return redirect("admin_camping_package_list")
