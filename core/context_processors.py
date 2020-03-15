from django.conf import settings


def language(request):
    """
    Sets language depending on the profile.
    """

    if request.user.is_authenticated:
        profile = request.user.profile
        return {'lan': profile.language}
    return {'lan': settings.LANGUAGE_CODE}
