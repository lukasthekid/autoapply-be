# Generated manually - Create SearchProfile table
# Note: Migration 0006 was modified to create SearchProfile, but the table was manually dropped.
# This migration creates the table if it doesn't exist, without trying to rename from JobAlert.

from django.db import migrations, models
import django.contrib.postgres.fields
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0009_remove_joblisting_search_keyword_search_location'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create the table if it doesn't exist (since it was manually dropped)
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS jobs_searchprofile (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(255),
                keyword VARCHAR(255) NOT NULL,
                location VARCHAR(255) NOT NULL,
                job_types TEXT[] DEFAULT '{}',
                experience_levels TEXT[] DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS jobs_searchprofile CASCADE;",
        ),
        # Create indexes if they don't exist
        migrations.RunSQL(
            sql=[
                "CREATE INDEX IF NOT EXISTS jobs_searchprofile_user_id_created_at_idx ON jobs_searchprofile(user_id, created_at DESC);",
                "CREATE INDEX IF NOT EXISTS jobs_searchprofile_keyword_location_idx ON jobs_searchprofile(keyword, location);",
                "CREATE INDEX IF NOT EXISTS jobs_searchprofile_created_at_idx ON jobs_searchprofile(created_at DESC);",
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS jobs_searchprofile_user_id_created_at_idx;",
                "DROP INDEX IF EXISTS jobs_searchprofile_keyword_location_idx;",
                "DROP INDEX IF EXISTS jobs_searchprofile_created_at_idx;",
            ],
        ),
    ]
