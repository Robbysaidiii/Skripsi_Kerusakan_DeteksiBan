from django.db import migrations, models


def seed_notifikasi(apps, schema_editor):
    Notifikasi = apps.get_model('deteksi', 'Notifikasi')
    Notifikasi.objects.bulk_create([
        Notifikasi(
            judul="Kondisi ban bermasalah terdeteksi",
            pesan="Deteksi ban menunjukkan retakan halus pada dinding ban depan kanan.",
            tag="Deteksi #DET-20240512-001",
            icon="peringatan",
            dibaca=False,
        ),
        Notifikasi(
            judul="Laporan siap diunduh",
            pesan="Laporan deteksi ban berhasil dibuat. Anda dapat mengunduhnya dalam format PDF.",
            tag="Laporan #LAP-20240512-015",
            icon="laporan",
            dibaca=False,
        ),
        Notifikasi(
            judul="Pengingat perawatan ban",
            pesan="Jangan lupa periksa tekanan angin dan kedalaman alur ban secara rutin untuk keamanan berkendara.",
            tag="",
            icon="lonceng",
            dibaca=False,
        ),
        Notifikasi(
            judul="Upload berhasil",
            pesan="Gambar ban yang Anda upload berhasil diproses.",
            tag="Deteksi #DET-20240511-009",
            icon="upload",
            dibaca=True,
        ),
        Notifikasi(
            judul="Jadwal perawatan berikutnya",
            pesan="Waktu yang disarankan untuk rotasi ban Anda adalah dalam 2.500 km lagi.",
            tag="",
            icon="jadwal",
            dibaca=True,
        ),
        Notifikasi(
            judul="Selamat datang di Deteksi Ban!",
            pesan="Terima kasih telah bergabung. Mulai deteksi pertama Anda sekarang.",
            tag="",
            icon="info",
            dibaca=True,
        ),
    ])


def unseed_notifikasi(apps, schema_editor):
    Notifikasi = apps.get_model('deteksi', 'Notifikasi')
    Notifikasi.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('deteksi', '0003_pengaturan_autentikasi_2fa_pengaturan_bahasa_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notifikasi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('judul', models.CharField(max_length=150)),
                ('pesan', models.TextField()),
                ('tag', models.CharField(blank=True, max_length=100)),
                ('icon', models.CharField(choices=[('peringatan', 'Peringatan'), ('laporan', 'Laporan'), ('lonceng', 'Lonceng'), ('upload', 'Upload'), ('jadwal', 'Jadwal'), ('info', 'Info')], default='info', max_length=16)),
                ('dibaca', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Notifikasi',
                'verbose_name_plural': 'Notifikasi',
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunPython(seed_notifikasi, unseed_notifikasi),
    ]
