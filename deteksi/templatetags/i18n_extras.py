"""
Filter template tambahan untuk menerjemahkan teks yang dibuat di backend
(bukan teks statis di HTML), misalnya nama kelas hasil deteksi ML
("Retak"/"Cracked") dan judul status ("Perhatian"/"Caution").

Kenapa terpisah dari i18n.py (dict `t`)?
- Teks-teks ini butuh "kunci dinamis" (code_label / status key) yang nilainya
  baru diketahui saat render (mis. tiap baris riwayat punya code_label
  beda-beda), sedangkan dict `t` di context processor cuma enak dipakai
  untuk key yang sudah pasti/statis (mis. {{ t.nav_beranda }}).
- Django template tidak bisa akses dict dengan variable key langsung
  (`t.somevar` tidak jalan kalau somevar isinya variable), makanya dibuat
  filter di sini: `{{ value|filter_name:bahasa_aktif }}`.

Cara pakai di template (bahasa_aktif sudah otomatis tersedia di semua
halaman lewat context processor bahasa_aktif):
    {% load i18n_extras %}
    {{ row.code_label|kelas_i18n:bahasa_aktif }}
    {{ d.key|status_title:bahasa_aktif }}
    {{ item.label|status_desc:bahasa_aktif }}
"""
from django import template

register = template.Library()

# code_label mentah dari model ML -> nama kelas ban per bahasa
KELAS_LABELS = {
    "normal": {"id": "Normal", "en": "Normal"},
    "cracked": {"id": "Retak", "en": "Cracked"},
    "Tear": {"id": "Robek", "en": "Torn"},
}

# Key status (BAIK/PERHATIAN/BERMASALAH) -> judul singkat per bahasa
STATUS_TITLES = {
    "BAIK": {"id": "Baik", "en": "Good"},
    "PERHATIAN": {"id": "Perhatian", "en": "Caution"},
    "BERMASALAH": {"id": "Bermasalah", "en": "Problem"},
}

# Key status -> deskripsi lengkap per bahasa (dipakai di halaman Laporan)
STATUS_DESCRIPTIONS = {
    "BAIK": {
        "id": "Ban dalam kondisi baik dan aman digunakan.",
        "en": "The tire is in good condition and safe to use.",
    },
    "PERHATIAN": {
        "id": "Ban masih dapat digunakan, namun ada beberapa bagian yang perlu diperhatikan.",
        "en": "The tire can still be used, but some parts need attention.",
    },
    "BERMASALAH": {
        "id": "Ban dalam kondisi kritis dan berisiko terhadap keselamatan berkendara.",
        "en": "The tire is in critical condition and poses a safety risk.",
    },
}


@register.filter
def kelas_i18n(code_label, bahasa):
    entry = KELAS_LABELS.get(code_label)
    if not entry:
        return code_label
    return entry.get(bahasa, entry["id"])


@register.filter
def status_title(status_key, bahasa):
    entry = STATUS_TITLES.get(status_key)
    if not entry:
        return status_key
    return entry.get(bahasa, entry["id"])


@register.filter
def status_desc(status_key, bahasa):
    entry = STATUS_DESCRIPTIONS.get(status_key)
    if not entry:
        return ""
    return entry.get(bahasa, entry["id"])


@register.filter
def get_item(d, key):
    """Akses dict dengan key dinamis di template: {{ mydict|get_item:mykey }}"""
    if d is None:
        return None
    try:
        return d.get(key)
    except AttributeError:
        return None
