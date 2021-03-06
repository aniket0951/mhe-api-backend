# Generated by Django 3.0.3 on 2020-02-26 18:39

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
                ('name', models.CharField(max_length=200, verbose_name='First Name')),
                ('code', models.CharField(max_length=300)),
                ('consultation_charges', models.IntegerField(default=0, null=True)),
                ('qualification', models.CharField(blank=True, max_length=300, null=True)),
                ('educational_degrees', models.CharField(blank=True, max_length=300, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('experience', models.IntegerField(blank=True, null=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital')),
                ('hospital_departments', models.ManyToManyField(blank=True, related_name='doctor', to='master_data.HospitalDepartment')),
                ('specialisations', models.ManyToManyField(blank=True, related_name='doctor', to='master_data.Specialisation')),
            ],
            options={
                'verbose_name': 'Doctor',
                'verbose_name_plural': 'Doctors',
                'permissions': (),
                'unique_together': {('code', 'hospital')},
            },
            bases=('users.baseuser',),
        ),
    ]
