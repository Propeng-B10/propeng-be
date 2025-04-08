# nilai/models.py (Contoh Lokasi File)

from django.db import models
from django.conf import settings # Cara standar mengambil model User
# Pastikan path import KomponenPenilaian benar
from komponenpenilaian.models import KomponenPenilaian

class Nilai(models.Model):
    # --- Pilihan Tipe Nilai ---
    PENGETAHUAN = 'pengetahuan'
    KETERAMPILAN = 'keterampilan'
    TIPE_NILAI_CHOICES = [
        (PENGETAHUAN, 'Pengetahuan'),
        (KETERAMPILAN, 'Keterampilan'),
    ]
    # --- Akhir Pilihan ---

    # Foreign Key ke User (Siswa) - Gunakan settings.AUTH_USER_MODEL
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Lebih baik pakai ini daripada import langsung
        on_delete=models.CASCADE,
        related_name='nilai_siswa' # Nama relasi dari User ke Nilai
    )

    # Foreign Key ke Komponen Penilaian
    # related_name di sini mungkin lebih cocok 'nilai_terkait' atau 'nilai_records'
    # karena 'nilai_siswa' sudah dipakai dari User
    komponen = models.ForeignKey(
        KomponenPenilaian, # Langsung referensi ke model yang diimport
        on_delete=models.CASCADE, # Atau PROTECT jika ingin mencegah penghapusan komponen jika ada nilai
        related_name='nilai_records',
        # null=True & blank=True mungkin tidak diperlukan jika setiap nilai HARUS punya komponen
        # Hapus jika komponen wajib ada
        null=True,
        blank=True
    )

    # Field Nilai (bolehin null mungkin oke jika nilai belum diinput)
    nilai = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )

    # --- Field Baru untuk Tipe Nilai ---
    tipe_nilai = models.CharField(
        max_length=15,
        choices=TIPE_NILAI_CHOICES,
        default=PENGETAHUAN,  # Defaultnya Pengetahuan
        # Tidak perlu null=True atau blank=True karena ada default
    )
    # --- Akhir Field Baru ---

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Pastikan hanya ada satu nilai per siswa per komponen PER TIPE NILAI
        unique_together = ('student', 'komponen', 'tipe_nilai') # Ini kuncinya!
        ordering = ['student', 'komponen', 'tipe_nilai']

    def __str__(self):
        score_display = str(self.nilai) if self.nilai is not None else "Kosong"
        nama_komponen_display = "N/A"
        nama_matpel_display = "N/A"
        if self.komponen:
            nama_komponen_display = self.komponen.namaKomponen
            if self.komponen.mataPelajaran:
                nama_matpel_display = self.komponen.mataPelajaran.nama # Asumsi field 'nama' di MataPelajaran

        # Dapatkan display name dari tipe_nilai
        tipe_display = self.get_tipe_nilai_display()

        # Format string termasuk tipe nilai
        # Ambil username siswa dengan aman
        student_display = str(self.student) # Default __str__ User atau username
        if hasattr(self.student, 'username'):
            student_display = self.student.username

        return f"{student_display} - {nama_komponen_display} ({nama_matpel_display}) [{tipe_display}]: {score_display}"