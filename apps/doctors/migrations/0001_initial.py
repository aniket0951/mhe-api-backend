# Generated by Django 3.0.3 on 2020-02-04 12:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('master_data', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('baseuser_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('code', models.SlugField(blank=True, null=True, unique=True)),
                ('designation', models.CharField(max_length=150)),
                ('awards_and_achievements', models.TextField(blank=True, null=True)),
                ('experience', models.IntegerField(blank=True, null=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(auto_now_add=True)),
                ('linked_hospitals', models.ManyToManyField(to='master_data.Hospital')),
                ('specialisations', models.ManyToManyField(to='master_data.Specialisation')),
            ],
            options={
                'verbose_name': 'Doctor',
                'verbose_name_plural': 'Doctors',
                'permissions': (),
            },
            bases=('users.baseuser',),
        ),
    ]
