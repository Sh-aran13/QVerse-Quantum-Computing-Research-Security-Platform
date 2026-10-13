"""
Guest & Public Research Access Helper
Enables friction-free open source access for students and researchers without requiring login/signup.
"""

from django.contrib.auth.models import User

def get_or_create_open_researcher(request=None):
    """
    Returns the authenticated user if logged in, or the shared default open-researcher.
    Ensures every student/researcher can build circuits and run algorithms immediately without login barriers.
    """
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        return request.user

    user, created = User.objects.get_or_create(
        username='open_researcher',
        defaults={
            'email': 'researcher@qverse.open',
            'first_name': 'Open',
            'last_name': 'Researcher'
        }
    )
    if created:
        user.set_unusable_password()
        user.save()
    return user
