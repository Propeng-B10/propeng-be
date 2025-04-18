from django.db import models
from django.conf import settings
# Import KomponenPenilaian dari lokasi yang benar
from komponenpenilaian.models import KomponenPenilaian

class Nilai(models.Model):
    # --- HAPUS Pilihan Tipe Nilai dari sini ---
    # PENGETAHUAN = 'pengetahuan'
    # KETERAMPILAN = 'keterampilan'
    # TIPE_NILAI_CHOICES = [...]
    # --- Akhir Hapus ---

    # Foreign Key ke User (Siswa)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='nilai_siswa'
    )

    # Foreign Key ke Komponen Penilaian
    komponen = models.ForeignKey(
        KomponenPenilaian,
        on_delete=models.PROTECT, # PROTECT agar komponen tidak bisa dihapus jika masih ada nilai terkait
        related_name='nilai_records',
        null=False, # Nilai harus selalu punya komponen
        blank=False
    )

    # Field Nilai
    nilai = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True # Boleh null jika belum diisi
    )

    # --- HAPUS Field tipe_nilai dari sini ---
    # tipe_nilai = models.CharField(...)
    # --- Akhir Hapus ---

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Unique berdasarkan siswa dan komponen saja
        unique_together = ('student', 'komponen')
        ordering = ['student', 'komponen']

    def __str__(self):
        score_display = str(self.nilai) if self.nilai is not None else "Kosong"
        nama_komponen_display = "N/A"
        nama_matpel_display = "N/A"
        tipe_komponen_display = "N/A" # Ambil dari komponen

        if self.komponen:
            nama_komponen_display = self.komponen.namaKomponen
            tipe_komponen_display = self.komponen.get_tipeKomponen_display() # Ambil display tipe
            if self.komponen.mataPelajaran:
                nama_matpel_display = self.komponen.mataPelajaran.nama # Asumsi field 'nama'

        student_display = str(self.student)
        if hasattr(self.student, 'username'):
            student_display = self.student.username

        # Format string tanpa tipe dari Nilai, tapi dari Komponen
        return f"{student_display} - {nama_komponen_display} ({nama_matpel_display}) [{tipe_komponen_display}]: {score_display}"