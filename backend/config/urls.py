from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        'name': 'LumaCart E-Commerce API',
        'version': '1.0.0',
        'status': 'operational',
        'documentation': {
            'auth': '/api/auth/',
            'products': '/api/products/',
            'categories': '/api/categories/',
            'cart': '/api/cart/',
            'orders': '/api/orders/',
            'reviews': '/api/reviews/',
            'wishlist': '/api/wishlist/',
            'notifications': '/api/notifications/',
            'admin_dashboard': '/admin/'
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api_root'),
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.catalog.urls')),
    path('api/', include('apps.cart.urls')),
    path('api/', include('apps.orders.urls')),
    path('api/', include('apps.payments.urls')),
    path('api/', include('apps.reviews.urls')),
    path('api/', include('apps.notifications.urls')),
]

def serve_frontend_index(request):
    return serve(request, 'index.html', document_root=settings.BASE_DIR.parent / 'frontend')

# Media and static serving with robust browser caching
def serve_cached_media(request, path, document_root=None):
    response = serve(request, path, document_root=document_root)
    # Enable browser caching for 30 days with immutable flag to eliminate re-fetch delay
    response['Cache-Control'] = 'public, max-age=2592000, immutable'
    return response

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_cached_media, {'document_root': settings.MEDIA_ROOT}),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Allow direct frontend page serving through Django dev server
    urlpatterns += [
        path('', serve_frontend_index, name='frontend_index'),
        re_path(r'^(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR.parent / 'frontend'}),
    ]


