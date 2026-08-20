Model sudah terpasang (v5_parallel, akurasi CV ~87.2%).

File yang ada di folder ini:
  - svm_best.pkl        (SVM RBF, C=50, gamma=0.005)
  - scaler.pkl          (StandardScaler)
  - pca.pkl             (PCA, 59 komponen, 95% variance)
  - label_encoder.pkl   (kelas: Tear, cracked, normal)
  - metadata.json       (info lengkap hasil training)

File-file ini dipakai oleh deteksi/ml/inference.py untuk memuat model dan
melakukan prediksi. Kalau mau mengganti dengan hasil training baru, cukup
timpa (overwrite) ke-5 file ini dengan nama yang sama persis.

Catatan versi: model ini dilatih dengan scikit-learn 1.6.1. Versi
scikit-learn sudah dikunci di requirements.txt (scikit-learn==1.6.1) agar
hasil prediksi konsisten dengan saat training — jangan upgrade versi ini
tanpa melatih ulang & menyimpan ulang model.
