from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0005_migrate_existing_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wordlist',
            name='share_code',
            field=models.CharField(db_index=True, max_length=8, unique=True),
        ),
        migrations.RemoveField(model_name='vocabulary', name='is_known'),
        migrations.RemoveField(model_name='vocabulary', name='level'),
        migrations.RemoveField(model_name='vocabulary', name='last_reviewed'),
    ]
