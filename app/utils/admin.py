from django.contrib import admin as django_admin


def register(model):
    """Register model in admin site.

    @register(Model)
    class ModelAdmin(admin.ModelAdmin):
        pass
    """

    def decorate(admin):
        django_admin.site.register(model, admin)
        return admin

    return decorate
