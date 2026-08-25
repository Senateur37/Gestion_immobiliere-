from .models import Notification, SiteSettings

def notifications(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
        return {'unread_notifications': unread_notifications, 'unread_notifications_count': unread_notifications.count()}
    return {'unread_notifications': [], 'unread_notifications_count': 0}

def site_settings_processor(request):
    return {
        'site_settings': SiteSettings.load()
    }
