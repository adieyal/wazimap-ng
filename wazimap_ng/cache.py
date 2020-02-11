from datetime import datetime
import logging

from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.views.decorators.cache import cache_page, cache_control

from .datasets.models import ProfileIndicator
from .points.models import Location, Category, Theme

logger = logging.getLogger(__name__)

profile_key = "etag-Profile-%s"
location_key = "etag-Location-%s"
location_theme_key = "etag-Location-Theme-%s"

def last_modified(request, key):
    last_modified = datetime(year=1970, month=1, day=1)
    c = cache.get(key)

    if c is not None:
        return c
    return last_modified

def etag_profile_updated(request, profile_id, geography_code):
    last_modified = last_modified_profile_updated(request, profile_id, geography_code)
    return str(last_modified)

def last_modified_profile_updated(request, profile_id, geography_code):
    key = profile_key % profile_id
    return last_modified(request, key)

def etag_point_updated(request, category_id):
    last_modified = last_modified_point_updated(request, category_id)
    return str(last_modified)

def last_modified_point_updated(request, category_id):
    key = location_key % category_id
    return last_modified(request, key)

########### Signals #################

@receiver(post_save, sender=ProfileIndicator)
def profile_updated(sender, instance, **kwargs):
    profile_id = instance.profile.id
    key = profile_key % profile_id
    cache.set(key, datetime.now())

@receiver(post_save, sender=Location)
def point_updated_location(sender, instance, **kwargs):
    point_updated_category(sender, instance.category, **kwargs)

@receiver(post_save, sender=Category)
def point_updated_category(sender, instance, **kwargs):
    category_id = instance.id
    key =location_key % category_id
    logger.debug(f"Set cache key: {key}")
    cache.set(key, datetime.now())

def cache_headers(func):
    return cache_control(max_age=0, public=True, must_revalidate=True)(func)

def cache_decorator(key, expiry=60*60*24*365):
    def _cache_decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = key
            if len(args) > 0:
                cache_key += "-".join(str(el) for el in args)

            if len(kwargs) > 0:
                cache_key += "-".join(f"{k}-{v}" for k, v in kwargs.items())

            cached_obj = cache.get(cache_key)
            if cached_obj is not None:
                print(f"Cache hit: {cache_key}")
                return cached_obj
            print(f"Cache miss: {cache_key}")


            obj = func(*args, **kwargs)
            cache.set(cache_key, obj, expiry)
            return obj
        return wrapper
    return _cache_decorator



