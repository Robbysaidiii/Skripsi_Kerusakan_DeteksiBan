from .i18n import get_text
from .models import Akun, Notifikasi, Pengaturan


def unread_notifications(request):
    """Sediakan jumlah notifikasi belum dibaca milik user yang sedang
    login untuk badge lonceng di header, tanpa perlu ditambahkan manual
    ke context tiap view."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"unread_notif_count": 0}
    count = Notifikasi.objects.filter(user=user, dibaca=False).count()
    return {"unread_notif_count": count}


def akun_aktif(request):
    """Sediakan data akun (nama & foto) untuk header di semua halaman,
    supaya konsisten dengan yang diubah lewat halaman Informasi Akun.
    Mengembalikan profil Akun milik user yang sedang login; None kalau
    belum login (mis. di halaman login/register)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"akun_aktif": None}
    return {"akun_aktif": Akun.get_for_user(user)}


def app_theme(request):
    """Sediakan tema tampilan (terang/gelap) tersimpan di semua halaman,
    bukan cuma di halaman Pengaturan, supaya berlaku ke seluruh aplikasi."""
    tema = Pengaturan.get_instance().tema
    return {"app_theme": tema}


def bahasa_aktif(request):
    """Sediakan kamus teks (`t`) sesuai bahasa yang tersimpan di
    Pengaturan, supaya SEMUA template bisa langsung pakai {{ t.key }}
    tanpa perlu ditambahkan manual di tiap view.

    Begitu bahasa diganti & disimpan lewat halaman Pengaturan, context
    processor ini otomatis kebaca ulang di setiap request berikutnya,
    jadi seluruh halaman ikut berubah bahasanya.
    """
    kode_bahasa = Pengaturan.get_instance().bahasa
    return {"t": get_text(kode_bahasa), "bahasa_aktif": kode_bahasa}


def format_tanggal_aktif(request):
    """Sediakan format tanggal (mis. "d M Y") sesuai yang dipilih user di
    halaman Pengaturan, supaya SEMUA halaman yang menampilkan tanggal
    (beranda, riwayat, laporan, profil, dll) otomatis ikut format itu
    lewat {{ sesuatu.tanggal|date:tgl_format }}, tanpa perlu di-hardcode
    per template."""
    return {"tgl_format": Pengaturan.get_instance().format_tanggal}
