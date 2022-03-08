from django.db import models
# from .utils import short_it


class UrlShorter(models.Model):
    short_url = models.CharField(unique=True, max_length=15)
    long_url = models.URLField()
    times_followed = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.short_url}'

    # def save(self, *args, **kwargs):
    #     if not self.short_url:
    #         self.short_url = short_it(self)

    #     super().save(*args, **kwargs)
