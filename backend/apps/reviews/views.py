from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Avg

from .models import ProductReview
from .serializers import ProductReviewSerializer
from apps.catalog.models import Product
from apps.orders.models import OrderItem

class ProductReviewListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, product_id):
        reviews = ProductReview.objects.filter(product_id=product_id, is_moderated=True)
        serializer = ProductReviewSerializer(reviews, many=True)
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 5.0
        return Response({
            'count': reviews.count(),
            'average_rating': round(avg_rating, 1),
            'reviews': serializer.data
        })

    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user purchased and received (delivered) this product
        delivered_item = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='delivered'
        ).exclude(review__isnull=False).first()

        if not delivered_item and not request.user.is_staff:
            return Response({
                'error': 'Only customers who have purchased and received this product can write a review.'
            }, status=status.HTTP_403_FORBIDDEN)

        rating = int(request.data.get('rating', 5))
        title = request.data.get('title', '').strip()
        comment = request.data.get('comment', '').strip()

        if not (1 <= rating <= 5) or not title or not comment:
            return Response({'error': 'Please provide a valid rating (1-5), title, and comment.'}, status=status.HTTP_400_BAD_REQUEST)

        review = ProductReview.objects.create(
            product=product,
            user=request.user,
            order_item=delivered_item,
            rating=rating,
            title=title,
            comment=comment,
            is_moderated=True
        )

        serializer = ProductReviewSerializer(review)
        return Response({
            'success': True,
            'message': 'Thank you! Your verified review has been published.',
            'review': serializer.data
        }, status=status.HTTP_201_CREATED)

class ReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            review = ProductReview.objects.get(id=pk, user=request.user)
        except ProductReview.DoesNotExist:
            return Response({'error': 'Review not found or unauthorized.'}, status=status.HTTP_404_NOT_FOUND)

        rating = request.data.get('rating')
        if rating:
            review.rating = int(rating)
        if 'title' in request.data:
            review.title = request.data['title']
        if 'comment' in request.data:
            review.comment = request.data['comment']
        review.save()

        return Response({'success': True, 'review': ProductReviewSerializer(review).data})

    def delete(self, request, pk):
        try:
            review = ProductReview.objects.get(id=pk, user=request.user)
            review.delete()
            return Response({'success': True, 'message': 'Review deleted successfully.'})
        except ProductReview.DoesNotExist:
            return Response({'error': 'Review not found or unauthorized.'}, status=status.HTTP_404_NOT_FOUND)
