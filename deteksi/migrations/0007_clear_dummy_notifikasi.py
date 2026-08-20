from django.db import migrations


def clear_dummy_notifikasi(apps, schema_editor):
    """Hapus notifikasi contoh (dummy) yang dulu di-seed lewat migrasi
    0004_notifikasi. Notifikasi sekarang dibuat otomatis dari aktivitas
    nyata (lihat predict_view di views.py), jadi data contoh ini tidak
    lagi relevan dan bikin badge lonceng seolah selalu ada 3 pesan baru
    padahal belum ada aktivitas apa pun."""
    Notifikasi = apps.get_model('deteksi', 'Notifikasi')
    Notifikasi.objects.filter(
        judul__in=[
            "Kondisi ban bermasalah terdeteksi",
            "Laporan siap diunduh",
            "Pengingat perawatan ban",
            "Upload berhasil",
            "Jadwal perawatan berikutnya",
            "Selamat datang di Deteksi Ban!",
        ],
        tag__in=[
            "Deteksi #DET-20240512-001",
            "Laporan #LAP-20240512-015",
            "",
            "Deteksi #DET-20240511-009",
        ],
    ).delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('deteksi', '0006_akun_aktif_akun_user_riwayat_user_alter_akun_peran_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_dummy_notifikasi, noop_reverse),
    ]
