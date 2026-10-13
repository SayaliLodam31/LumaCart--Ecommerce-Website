from rest_framework import viewsets, filters, status, generics
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.db.models import Q, Avg, Count
from django.db import transaction

from .models import Category, Brand, Size, Colour, Product, ProductImage, ProductVariant, Inventory, HomeBanner, AuditLog, Wishlist, WishlistItem
from .serializers import (
    CategorySerializer,
    BrandSerializer,
    SizeSerializer,
    ColourSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductVariantSerializer,
    HomeBannerSerializer,
    AuditLogSerializer,
    WishlistSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

class SizeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [AllowAny]

class ColourViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Colour.objects.all()
    serializer_class = ColourSerializer
    permission_classes = [AllowAny]

class HomeBannerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HomeBanner.objects.filter(is_active=True)
    serializer_class = HomeBannerSerializer
    permission_classes = [AllowAny]

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images', 'variants__size', 'variants__colour', 'variants__inventory', 'reviews')
        params = self.request.query_params

        # Search query (debounced from frontend)
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(brand__name__icontains=search) |
                Q(category__name__icontains=search)
            )

        # Filters
        category = params.get('category')
        if category:
            cat_slug = category.lower().strip()
            if cat_slug in ('womens-clothing', 'women-clothing', 'womens'):
                queryset = queryset.filter(Q(category__slug='womens-clothing') | (Q(gender='women') & Q(category__slug__in=['womens-clothing', 'clothing'])))
            elif cat_slug in ('mens-clothing', 'men-clothing', 'mens'):
                queryset = queryset.filter(Q(category__slug='mens-clothing') | (Q(gender='men') & Q(category__slug__in=['mens-clothing', 'clothing'])))
            elif cat_slug in ('clothing', 'apparel'):
                queryset = queryset.filter(category__slug__in=['womens-clothing', 'mens-clothing', 'clothing'])
            elif cat_slug in ('bags',):
                queryset = queryset.filter(category__slug='bags')
            elif cat_slug in ('jewellery', 'jewelry'):
                queryset = queryset.filter(category__slug__in=['jewellery', 'jewelry'])
            elif cat_slug in ('accessories',):
                queryset = queryset.filter(category__slug='accessories')
            elif cat_slug in ('jewelry-and-accessories', 'jewellery-and-accessories'):
                queryset = queryset.filter(category__slug__in=['jewelry-and-accessories', 'jewellery', 'accessories', 'bags'])
            elif cat_slug in ('shoes', 'footwear'):
                queryset = queryset.filter(category__slug__in=['shoes', 'footwear'])
            else:
                queryset = queryset.filter(Q(category__slug__iexact=category) | Q(category__name__iexact=category))

        brand = params.get('brand')
        if brand:
            queryset = queryset.filter(Q(brand__slug=brand) | Q(brand__name__iexact=brand))

        gender = params.get('gender')
        if gender:
            queryset = queryset.filter(gender__iexact=gender)

        size = params.get('size')
        if size:
            queryset = queryset.filter(variants__size__name__iexact=size, variants__inventory__stock_quantity__gt=0).distinct()

        colour = params.get('colour')
        if colour:
            queryset = queryset.filter(variants__colour__name__iexact=colour).distinct()

        min_price = params.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(base_price__gte=float(min_price))
            except ValueError:
                pass

        max_price = params.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(base_price__lte=float(max_price))
            except ValueError:
                pass

        is_featured = params.get('featured')
        if is_featured and is_featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)

        is_new_arrival = params.get('new_arrival')
        if is_new_arrival and is_new_arrival.lower() == 'true':
            queryset = queryset.filter(is_new_arrival=True)

        in_stock = params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(variants__inventory__stock_quantity__gt=0).distinct()

        # Sorting
        ordering = params.get('ordering', '-created_at')
        if ordering == 'price_low_high':
            queryset = queryset.order_by('base_price')
        elif ordering == 'price_high_low':
            queryset = queryset.order_by('-base_price')
        elif ordering == 'popular':
            queryset = queryset.order_by('-total_sold')
        elif ordering == 'newest':
            queryset = queryset.order_by('-created_at')
        elif ordering == 'rating':
            queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
        else:
            queryset = queryset.order_by(ordering)

        return queryset

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_products = self.get_queryset().filter(is_featured=True)[:8]
        serializer = ProductListSerializer(featured_products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        new_products = self.get_queryset().filter(is_new_arrival=True)[:8]
        serializer = ProductListSerializer(new_products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def best_sellers(self, request):
        best = self.get_queryset().order_by('-total_sold')[:8]
        serializer = ProductListSerializer(best, many=True, context={'request': request})
        return Response(serializer.data)

class AdminCatalogViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('category', 'brand').prefetch_related('variants__inventory')
    serializer_class = ProductDetailSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        product = self.get_object()
        variant_id = request.data.get('variant_id')
        new_stock = request.data.get('stock')

        if variant_id is None or new_stock is None:
            return Response({'error': 'variant_id and stock are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                variant = product.variants.get(id=variant_id)
                inventory, _ = Inventory.objects.get_or_create(variant=variant)
                old_stock = inventory.stock_quantity
                inventory.stock_quantity = int(new_stock)
                inventory.save()

                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE_STOCK',
                    model_name='Inventory',
                    object_id=str(variant.sku),
                    changes_json={'old_stock': old_stock, 'new_stock': int(new_stock)}
                )

                # Send WebSocket notification for realtime inventory update
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'stock_updates',
                        {
                            'type': 'stock_updated',
                            'product_id': product.id,
                            'variant_id': variant.id,
                            'sku': variant.sku,
                            'available_stock': inventory.available_stock
                        }
                    )
                except Exception:
                    pass

                return Response({'success': True, 'variant_id': variant.id, 'new_stock': inventory.available_stock})
        except ProductVariant.DoesNotExist:
            return Response({'error': 'Variant not found'}, status=status.HTTP_404_NOT_FOUND)

class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        serializer = WishlistSerializer(wishlist, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)

        serializer = WishlistSerializer(wishlist, context={'request': request})
        msg = f"Added '{product.title}' to your wishlist." if created else f"'{product.title}' is already in your wishlist."
        return Response({'success': True, 'message': msg, 'wishlist': serializer.data})

    def delete(self, request, pk=None):
        product_id = pk or request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        WishlistItem.objects.filter(wishlist=wishlist, product_id=product_id).delete()

        serializer = WishlistSerializer(wishlist, context={'request': request})
        return Response({'success': True, 'message': 'Item removed from wishlist.', 'wishlist': serializer.data})

