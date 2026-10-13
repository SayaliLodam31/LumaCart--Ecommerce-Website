from django.urls import path
from .views import NotificationListView, MarkNotificationReadView

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification_read_single'),
    path('notifications/read-all/', MarkNotificationReadView.as_view(), name='notification_read_all'),
]
