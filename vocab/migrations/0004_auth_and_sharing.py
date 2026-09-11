import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vocab', '0003_vocabulary_last_reviewed_vocabulary_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='wordlist',
            name='owner',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='word_lists',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='wordlist',
            name='share_code',
            field=models.CharField(db_index=True, max_length=8, null=True),
        ),
        migrations.CreateModel(
            name='WordProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_known', models.BooleanField(default=False)),
                ('level', models.IntegerField(default=0)),
                ('correct_count', models.IntegerField(default=0)),
                ('wrong_count', models.IntegerField(default=0)),
                ('last_reviewed', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress', to=settings.AUTH_USER_MODEL)),
                ('vocabulary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress', to='vocab.vocabulary')),
            ],
            options={
                'unique_together': {('user', 'vocabulary')},
            },
        ),
        migrations.AddIndex(
            model_name='wordprogress',
            index=models.Index(fields=['user', 'is_known'], name='vocab_wordp_user_id_c4cd3f_idx'),
        ),
        migrations.CreateModel(
            name='JoinedList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='joined_lists', to=settings.AUTH_USER_MODEL)),
                ('word_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='joined_by', to='vocab.wordlist')),
            ],
            options={
                'ordering': ['-joined_at'],
                'unique_together': {('user', 'word_list')},
            },
        ),
    ]
