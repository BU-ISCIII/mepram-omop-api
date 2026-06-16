from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update the default Django superuser for local/test deployments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Create/update the user even when MEPRAM_CREATE_DEFAULT_SUPERUSER is false.",
        )

    def handle(self, *args, **options):
        if not settings.MEPRAM_CREATE_DEFAULT_SUPERUSER and not options["force"]:
            self.stdout.write("Default superuser creation disabled")
            return

        username = settings.DJANGO_SUPERUSER_USERNAME.strip()
        email = settings.DJANGO_SUPERUSER_EMAIL.strip()
        password = settings.DJANGO_SUPERUSER_PASSWORD

        if not username:
            raise CommandError("DJANGO_SUPERUSER_USERNAME cannot be empty")
        if not password:
            raise CommandError("DJANGO_SUPERUSER_PASSWORD cannot be empty")

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(username=username)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} default superuser '{username}'"))
