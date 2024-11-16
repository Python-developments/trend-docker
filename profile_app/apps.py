from django.apps import AppConfig

class ProfileAppConfig(AppConfig):
    name = 'profile_app'

    def ready(self):
        import profile_app.signals
