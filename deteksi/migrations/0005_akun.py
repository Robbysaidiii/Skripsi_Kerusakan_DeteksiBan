from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deteksi', '0004_notifikasi'),
    ]

    operations = [
        migrations.CreateModel(
            name='Akun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('foto', models.ImageField(blank=True, null=True, upload_to='akun/')),
                ('nama_lengkap', models.CharField(default='Pengguna Baru', max_length=150)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('email_terverifikasi', models.BooleanField(default=False)),
                ('telepon', models.CharField(blank=True, max_length=32)),
                ('peran', models.CharField(choices=[('admin', 'Admin'), ('pengguna', 'Pengguna')], default='admin', max_length=16)),
                ('kode_pengguna', models.CharField(blank=True, max_length=32, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Akun',
                'verbose_name_plural': 'Akun',
            },
        ),
    ]
