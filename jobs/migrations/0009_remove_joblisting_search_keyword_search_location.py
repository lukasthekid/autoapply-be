# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0008_remove_joblisting_is_enriched'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='joblisting',
            name='search_keyword',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='search_location',
        ),
    ]
