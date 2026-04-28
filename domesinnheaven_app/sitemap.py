from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Blog, Activity, CampingPackage


class StaticViewSitemap(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 1.0

    def items(self):
        return [
            "home",
            "about",
            "trips",
            "team",
            "image_gallery",
            "blog",
            "activity_list",
            "camping_packages",
            "contact",
            "booking",
        ]

    def location(self, item):
        return reverse(item)


class BlogSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Blog.objects.all()

    def location(self, obj):
        return reverse("blog_single", kwargs={"slug": obj.slug})


class CampingPackageSitemap(Sitemap):
    priority = 0.9
    changefreq = "monthly"

    def items(self):
        return CampingPackage.objects.all()

    def location(self, obj):
        return reverse("camping_package_single", kwargs={"slug": obj.slug})


class ActivitySitemap(Sitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        return Activity.objects.all()

    def location(self, obj):
        return reverse("activity_single", kwargs={"slug": obj.slug})
