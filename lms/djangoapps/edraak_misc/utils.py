from django.conf import settings
from django.core.cache import cache
from xmodule.modulestore.django import modulestore

from courseware.access import has_access
from courseware.grades import grade
from opaque_keys.edx import locator


def cached_function(cache_key_format, timeout=30):
    """
    Decorator to cache heavy functions.

    Use it as the following:
    @cached_function("module.add_numbers.{0}.{1}", 30)
    def add_numbers(a, b):
        return a + b

    """
    def the_decorator(func):

        def cached_func(*args, **kwargs):
            cache_key = cache_key_format.format(*args, **kwargs)
            cached_result = cache.get(cache_key)

            if cached_result is not None:
                return cached_result
            else:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
                return result

        return cached_func

    return the_decorator


@cached_function(
    cache_key_format='edraak_misc.utils.is_student_pass.{0.id}.{2}',
    timeout=60*5  # Cache up to 5 minutes
)
def is_student_pass(user, request, course_id):
    course_key = locator.CourseLocator.from_string(course_id)
    course = modulestore().get_course(course_key)

    if not settings.FEATURES.get('ENABLE_ISSUE_CERTIFICATE'):
        return False

    # If user is course staff don't grade the user
    if has_access(user, 'staff', course):
        return True

    return bool(grade(user, request, course)['grade'])


def is_certificate_allowed(user, course):
    if not settings.FEATURES.get('ENABLE_ISSUE_CERTIFICATE'):
        return False

    return course.may_certify() or has_access(user, 'staff', course.id)


def sort_closed_courses_to_bottom(courses):
    """
    Sorts the courses by their `has_ended()`, open courses come first.
    """

    open_courses = [course for course in courses if not course.has_ended()]
    ended_courses = [course for course in courses if course.has_ended()]

    return open_courses + ended_courses


def filter_invitation_only_courses(courses):
    """
    Filter out the courses with invitation_only flag set to true.
    """

    return [course for course in courses if not course.invitation_only]


def edraak_courses_logic(courses):
    courses = filter_invitation_only_courses(courses)
    courses = sort_closed_courses_to_bottom(courses)
    return courses


def get_absolute_url_prefix(request):
    schema = 'https' if request.is_secure() else 'http'
    prefix = '{schema}://{host}'.format(schema=schema, host=settings.SITE_NAME)
    return prefix
