"""
Modul ekstraksi fitur — HARUS identik dengan pipeline training (v5 Parallel)
agar dimensi & urutan fitur cocok dengan scaler.pkl & pca.pkl yang sudah dilatih.

Urutan fitur: LBP(multi) + GLCM + Gabor + Wavelet + Canny(grid) + HuMoments
"""
import numpy as np
from PIL import Image, ImageOps
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from skimage.color import rgb2gray
from skimage.filters import gabor
import cv2
import pywt

# ── KONFIGURASI (harus sama persis dengan skrip training) ──────────
IMG_SIZE = (224, 224)

LBP_CONFIGS = [
    (1, 8, 'uniform', 256),
    (2, 16, 'uniform', 256),
    (3, 24, 'uniform', 256),
]

GLCM_DISTANCES = [1, 2, 3, 5]
GLCM_ANGLES = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]
GLCM_PROPS = ['contrast', 'homogeneity', 'energy',
              'correlation', 'dissimilarity', 'ASM']

GABOR_FREQUENCIES = [0.05, 0.1, 0.2, 0.3, 0.4]
GABOR_THETAS = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]

WAVELET_NAME = 'db4'
WAVELET_LEVEL = 3

CANNY_LOW = 50
CANNY_HIGH = 150
CANNY_GRID = 8


def apply_clahe(img_gray):
    img_uint8 = (img_gray * 255).astype(np.uint8)
    pil = Image.fromarray(img_uint8)
    eq = ImageOps.equalize(pil)
    return np.array(eq).astype(np.float64) / 255.0


def extract_lbp_feat(img_gray):
    feats = []
    for radius, n_points, method, bins in LBP_CONFIGS:
        lbp = local_binary_pattern(img_gray, n_points, radius, method=method)
        hist, _ = np.histogram(lbp.ravel(), bins=bins, range=(0, bins), density=True)
        feats.append(hist.astype(np.float32))
    return np.concatenate(feats)


def extract_glcm_feat(img_gray):
    img_uint8 = (img_gray * 255).astype(np.uint8)
    glcm = graycomatrix(
        img_uint8,
        distances=GLCM_DISTANCES,
        angles=GLCM_ANGLES,
        levels=256,
        symmetric=True,
        normed=True
    )
    feats = []
    for prop in GLCM_PROPS:
        val = graycoprops(glcm, prop).ravel()
        feats.append(val)
    return np.concatenate(feats)


def extract_gabor_feat(img_gray):
    feats = []
    for freq in GABOR_FREQUENCIES:
        for theta in GABOR_THETAS:
            real, imag = gabor(img_gray, frequency=freq, theta=theta)
            magnitude = np.sqrt(real ** 2 + imag ** 2)
            feats.extend([
                float(magnitude.mean()),
                float(magnitude.std()),
                float(magnitude.max()),
                float(np.percentile(magnitude, 75)),
                float(np.percentile(magnitude, 25)),
            ])
    return np.array(feats, dtype=np.float32)


def extract_wavelet_feat(img_gray):
    feats = []
    coeffs = pywt.wavedec2(img_gray, wavelet=WAVELET_NAME, level=WAVELET_LEVEL)
    for level_coeffs in coeffs[1:]:
        for subband in level_coeffs:
            abs_sub = np.abs(subband)
            feats.extend([
                float(subband.mean()),
                float(subband.std()),
                float(abs_sub.mean()),
                float(np.sqrt(np.mean(subband ** 2))),
                float(np.percentile(abs_sub, 90)),
                float(subband.max() - subband.min()),
            ])
    return np.array(feats, dtype=np.float32)


def extract_canny_feat(img_gray):
    img_uint8 = (img_gray * 255).astype(np.uint8)
    edges = cv2.Canny(img_uint8, CANNY_LOW, CANNY_HIGH)
    global_d = edges.sum() / (edges.shape[0] * edges.shape[1] * 255.0)
    h, w = edges.shape
    gh, gw = h // CANNY_GRID, w // CANNY_GRID
    grid_d = []
    for r in range(CANNY_GRID):
        for c in range(CANNY_GRID):
            patch = edges[r * gh:(r + 1) * gh, c * gw:(c + 1) * gw]
            d = patch.sum() / (patch.size * 255.0 + 1e-10)
            grid_d.append(d)
    return np.array([global_d] + grid_d, dtype=np.float32)


def extract_hu_moments(img_gray):
    img_uint8 = (img_gray * 255).astype(np.uint8)
    moments = cv2.moments(img_uint8)
    hu = cv2.HuMoments(moments).flatten()
    hu_log = -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)
    return hu_log.astype(np.float32)


def extract_all_from_pil(pil_image):
    """
    Terima objek PIL.Image (RGB), kembalikan 1 vektor fitur (float32)
    dengan urutan: LBP + GLCM + Gabor + Wavelet + Canny + HuMoments
    """
    img_rgb = np.array(pil_image.convert("RGB").resize(IMG_SIZE, Image.LANCZOS))
    img_gray = rgb2gray(img_rgb)
    img_gray = apply_clahe(img_gray)

    lbp_f = extract_lbp_feat(img_gray)
    glcm_f = extract_glcm_feat(img_gray)
    gabor_f = extract_gabor_feat(img_gray)
    wavelet_f = extract_wavelet_feat(img_gray)
    canny_f = extract_canny_feat(img_gray)
    hu_f = extract_hu_moments(img_gray)

    return np.concatenate([lbp_f, glcm_f, gabor_f, wavelet_f, canny_f, hu_f])
