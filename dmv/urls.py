"""
URL configuration for dmv project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
# from cms.api import api_router  # CMS API disabled

from dmv.health import health

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # Wagtail admin (CMS backend - keep for content management)
    path('cms/', include(wagtailadmin_urls)),
    
    # CMS custom views (import, etc.)
    path('cms-admin/', include('cms.urls')),
    # path('documents/', include(wagtaildocs_urls)),
    
    # API endpoints
    path("api/health/", health, name="health"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/accounts/", include("accounts.urls")),
    path("api/onboarding/", include("onboarding.urls")),
    path("api/learning/", include("learning.urls")),
    path("api/site-details/", include("site_details.urls")),
    # path("api/cms/", api_router.urls),  # CMS API disabled
]

# Wagtail pages (should be last to not override other URLs)
# urlpatterns += [
#     path("", include(wagtail_urls)),  # CMS frontend pages disabled
# ]

# Serve MEDIA even when DEBUG=False so the Next.js image optimizer can fetch
# http://api:8000/media/... on the Docker network. Public browsers still hit
# host nginx at api.mytestdmv.com/media/ (see docs/DOCKER.md).
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", static_serve, {"document_root": settings.MEDIA_ROOT}),
]

# Static files via Django only in development (prod uses collectstatic + nginx).
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
