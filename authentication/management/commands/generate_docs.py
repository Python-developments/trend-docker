from django.core.management.base import BaseCommand
from django.urls import reverse
from django.urls.resolvers import get_resolver
from django.utils.text import slugify
from rest_framework.schemas import get_schema_view
from rest_framework.compat import coreapi

class Command(BaseCommand):
    help = 'Generate Markdown documentation for Django project'

    def handle(self, *args, **kwargs):
        """
        Entry point of the management command.
        """
        markdown_content = ""

        # Generate documentation for models
        markdown_content += self.generate_model_documentation()

        # Generate documentation for serializers
        markdown_content += self.generate_serializer_documentation()

        # Generate documentation for views
        markdown_content += self.generate_view_documentation()

        # Generate documentation for URLs
        markdown_content += self.generate_url_documentation()

        # Save the Markdown content to a file
        with open('documentation.md', 'w') as f:
            f.write(markdown_content)

        self.stdout.write(self.style.SUCCESS('Markdown documentation generated successfully.'))

    def generate_model_documentation(self):
        """
        Generate Markdown documentation for models.
        """
        from django.apps import apps

        model_documentation = "## Models\n\n"

        for model in apps.get_models():
            model_documentation += f"### {model.__name__}\n\n"
            model_documentation += f"{model.__doc__}\n\n" if model.__doc__ else ""
            model_documentation += "```python\n"
            model_documentation += f"from {model.__module__} import {model.__name__}\n"
            model_documentation += f"{model.__str__.__doc__}\n\n" if model.__str__.__doc__ else ""
            for field in model._meta.fields:
                model_documentation += f"{field.name}: {field.get_internal_type()}\n"
                model_documentation += f"    {field.verbose_name}\n" if field.verbose_name else ""
                model_documentation += f"    {field.help_text}\n" if field.help_text else ""
            model_documentation += "```\n\n"

        return model_documentation

    def generate_serializer_documentation(self):
        """
        Generate Markdown documentation for serializers.
        """
        from rest_framework.serializers import BaseSerializer

        serializer_documentation = "## Serializers\n\n"

        for subclass in BaseSerializer.__subclasses__():
            serializer_documentation += f"### {subclass.__name__}\n\n"
            serializer_documentation += f"{subclass.__doc__}\n\n" if subclass.__doc__ else ""
            serializer_documentation += "```python\n"
            serializer_documentation += f"from {subclass.__module__} import {subclass.__name__}\n"
            serializer_documentation += "```\n\n"

        return serializer_documentation

    def generate_view_documentation(self):
        """
        Generate Markdown documentation for views.
        """
        from rest_framework.views import APIView

        view_documentation = "## Views\n\n"

        for subclass in APIView.__subclasses__():
            view_documentation += f"### {subclass.__name__}\n\n"
            view_documentation += f"{subclass.__doc__}\n\n" if subclass.__doc__ else ""
            view_documentation += "```python\n"
            view_documentation += f"from {subclass.__module__} import {subclass.__name__}\n"
            view_documentation += "```\n\n"

        return view_documentation

    def generate_url_documentation(self):
        """
        Generate Markdown documentation for URLs.
        """
        url_documentation = "## URLs\n\n"

        # Get all URL patterns in the project
        urlconf = get_resolver().url_patterns

        def get_urls(patterns, prefix=''):
            """
            Recursively build a list of URL patterns.
            """
            urls = []
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    urls += get_urls(pattern.url_patterns, prefix + pattern.pattern.regex.pattern)
                if hasattr(pattern, 'callback'):
                    urls.append((prefix + pattern.pattern.regex.pattern, pattern.callback.__doc__))
            return urls

        for (pattern, docstring) in get_urls(urlconf):
            url_documentation += f"- `{pattern}`: {docstring}\n\n" if docstring else ""

        return url_documentation
