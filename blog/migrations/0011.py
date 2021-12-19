from django.db import migrations
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_auto_20210225_2142'),
    ]

    operations = [
        migrations.RunSQL("ALTER TABLE blog_post ADD FULLTEXT(title, text)")
    ]
