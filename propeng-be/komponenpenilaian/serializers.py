from rest_framework import serializers
from .models import KomponenPenilaian
from matapelajaran.models import MataPelajaran

class KomponenPenilaianSerializer(serializers.ModelSerializer):
    mataPelajaran = serializers.PrimaryKeyRelatedField(queryset=MataPelajaran.objects.all(), required=True)

    class Meta:
        model = KomponenPenilaian
        fields = ['id', 'namaKomponen', 'bobotKomponen', 'mataPelajaran']

    def validate_mataPelajaran(self, value):
        if value.isDeleted:
            raise serializers.ValidationError(f"Mata Pelajaran dengan ID {value.id} sudah dihapus.")
        return value

    def validate(self, data):
        instance = getattr(self, 'instance', None)
        nama_komponen = data.get('namaKomponen')
        mata_pelajaran = data.get('mataPelajaran')

        # Nama Komponen harus bersifat unik dalam objek Mata Pelajaran tersebut saja
        if nama_komponen and mata_pelajaran:
            existing = KomponenPenilaian.objects.filter(
                namaKomponen__iexact=nama_komponen,
                mataPelajaran=mata_pelajaran
            )
            if instance:
                existing = existing.exclude(pk=instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    {"namaKomponen": "Komponen dengan nama ini sudah ada dalam mata pelajaran tersebut."}
                )

        return data

    def create(self, data):
        return KomponenPenilaian.objects.create(**data)

    def update(self, instance, data):
        instance.namaKomponen = data.get('namaKomponen', instance.namaKomponen)
        instance.bobotKomponen = data.get('bobotKomponen', instance.bobotKomponen)
        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.mataPelajaran:
            rep['mataPelajaran'] = {
                'id': instance.mataPelajaran.id,
                'nama': instance.mataPelajaran.nama,
                'tahunAjaran': instance.mataPelajaran.tahunAjaran.id if instance.mataPelajaran.tahunAjaran else None
            }
        return rep