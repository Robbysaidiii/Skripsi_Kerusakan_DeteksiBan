"""
Modul inferensi: memuat model (svm_best.pkl, scaler.pkl, pca.pkl,
label_encoder.pkl, metadata.json) sekali saat server start, lalu
menyediakan fungsi predict(pil_image) -> dict hasil deteksi.
"""
import os
import json
import threading

import joblib

from .feature_extraction import extract_all_from_pil

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")

# Info tampilan per kelas (label kode dari training -> label tingkat
# keparahan (severity) + nama kelas teknis + teks bantu untuk UI)
CLASS_DISPLAY = {
    "normal": {
        "label": "BAIK",
        "kelas": "Normal",
        "desc": "Ban masih dalam kondisi baik dan aman digunakan.",
        "color": "green",
        "rekomendasi": "Ban dalam kondisi baik dan aman digunakan. Tetap lakukan "
                        "pengecekan rutin secara berkala.",
    },
    "cracked": {
        "label": "PERHATIAN",
        "kelas": "Retak",
        "desc": "Terdeteksi retak pada permukaan ban. Ban masih dapat digunakan, "
                "namun perlu diperhatikan.",
        "color": "amber",
        "rekomendasi": "Terdeteksi retak pada permukaan ban. Disarankan untuk "
                        "memeriksakan ban ke bengkel dan memantau perkembangan retakan.",
    },
    "Tear": {
        "label": "BERMASALAH",
        "kelas": "Robek",
        "desc": "Terdeteksi robek pada ban. Kondisi ban buruk dan berisiko.",
        "color": "red",
        "rekomendasi": "Terdeteksi robek pada ban. Segera ganti ban untuk "
                        "menghindari risiko kecelakaan.",
    },
}

_lock = threading.Lock()
_state = {"loaded": False, "error": None}


class ModelBundle:
    scaler = None
    pca = None
    svm = None
    label_encoder = None
    metadata = {}


bundle = ModelBundle()


def _path(name):
    return os.path.join(MODEL_DIR, name)


def load_models(force=False):
    """Load semua artefak model dari MODEL_DIR. Aman dipanggil berkali-kali."""
    with _lock:
        if _state["loaded"] and not force:
            return True, None
        required = ["scaler.pkl", "pca.pkl", "svm_best.pkl", "label_encoder.pkl"]
        missing = [f for f in required if not os.path.exists(_path(f))]
        if missing:
            msg = (
                "File model belum ditemukan di deteksi/ml_models/: "
                + ", ".join(missing)
                + ". Silakan letakkan file .pkl hasil training di folder tersebut."
            )
            _state["loaded"] = False
            _state["error"] = msg
            return False, msg
        try:
            bundle.scaler = joblib.load(_path("scaler.pkl"))
            bundle.pca = joblib.load(_path("pca.pkl"))
            bundle.svm = joblib.load(_path("svm_best.pkl"))
            bundle.label_encoder = joblib.load(_path("label_encoder.pkl"))
            meta_path = _path("metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    bundle.metadata = json.load(f)
            else:
                bundle.metadata = {}
            _state["loaded"] = True
            _state["error"] = None
            return True, None
        except Exception as e:  # pragma: no cover
            _state["loaded"] = False
            _state["error"] = f"Gagal memuat model: {e}"
            return False, _state["error"]


def is_ready():
    return _state["loaded"]


def get_error():
    return _state["error"]


def predict(pil_image):
    """
    Jalankan pipeline lengkap: ekstraksi fitur -> scaler -> pca -> svm.
    Return dict berisi label, confidence, dan breakdown probabilitas per kelas.
    """
    ok, err = load_models()
    if not ok:
        return {"success": False, "error": err}

    try:
        feat = extract_all_from_pil(pil_image)
        feat_sc = bundle.scaler.transform(feat.reshape(1, -1))
        feat_pca = bundle.pca.transform(feat_sc)

        pred_idx = bundle.svm.predict(feat_pca)[0]
        proba = bundle.svm.predict_proba(feat_pca)[0]
        code_label = bundle.label_encoder.inverse_transform([pred_idx])[0]

        classes = list(bundle.label_encoder.classes_)
        proba_map = {cls: round(float(p) * 100, 2) for cls, p in zip(classes, proba)}
        confidence = round(float(proba.max()) * 100, 2)

        info = CLASS_DISPLAY.get(code_label, {
            "label": str(code_label).upper(),
            "kelas": str(code_label),
            "desc": "",
            "color": "gray",
            "rekomendasi": "",
        })

        breakdown = []
        for cls in classes:
            disp = CLASS_DISPLAY.get(cls, {"label": cls, "kelas": cls, "color": "gray"})
            breakdown.append({
                "code": cls,
                "kelas": disp["kelas"],
                "label": disp["label"],
                "color": disp["color"],
                "value": proba_map.get(cls, 0),
            })
        breakdown.sort(key=lambda x: x["value"], reverse=True)

        return {
            "success": True,
            "code_label": code_label,
            "kelas": info["kelas"],
            "label": info["label"],
            "desc": info["desc"],
            "color": info["color"],
            "confidence": confidence,
            "rekomendasi": info["rekomendasi"],
            "breakdown": breakdown,
        }
    except Exception as e:
        return {"success": False, "error": f"Gagal melakukan prediksi: {e}"}


# Coba load saat modul diimpor (tidak fatal jika gagal / file belum ada)
load_models()
