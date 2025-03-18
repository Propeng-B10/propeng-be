from django.db import IntegrityError, transaction
from rest_framework import serializers
from .models import MataPelajaran
from user.models import Teacher, Student, User
from tahunajaran.models import TahunAjaran, Angkatan

class MataPelajaranSerializer(serializers.ModelSerializer):
    print("🔹 MataPelajaranSerializer")
    kategoriMatpel = serializers.ChoiceField(choices=MataPelajaran.MATPEL_CATEGORY)
    teacher = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)
    siswa_terdaftar = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    tahunAjaran = serializers.IntegerField(write_only=True)
    angkatan = serializers.IntegerField(write_only=True, required=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = MataPelajaran
        fields = ['id', 'kategoriMatpel', 'nama', 'kode', 'angkatan','tahunAjaran', 'teacher', 'siswa_terdaftar', 'status']
        read_only_fields = ['kode']

    def get_status(self, obj):
        return "Active" if obj.isActive else "Inactive"

    def to_internal_value(self, data):
        if 'status' in data:
            data['isActive'] = data['status'] == "Active"
            del data['status']
        return super().to_internal_value(data)

    def validate_teacher(self, value):
        """
        Validate that the teacher exists and is not deleted.
        """
        try:
            teacher = Teacher.objects.get(user_id=value.id)
            if teacher.isDeleted:
                raise serializers.ValidationError(f"Teacher with ID {value.id} exists but is marked as deleted")
            return value
        except Teacher.DoesNotExist:
            raise serializers.ValidationError(f"No teacher found with ID {value.id}")

    def validate_siswa_terdaftar(self, value):
        """
        Validate that all students exist and are not deleted.
        """
        valid_students = []
        errors = []
        
        for user in value:
            try:
                student = Student.objects.get(user_id=user.id)
                if student.isDeleted:
                    errors.append(f"Student with ID {user.id} exists but is marked as deleted")
                else:
                    valid_students.append(user)
            except Student.DoesNotExist:
                errors.append(f"No student found with ID {user.id}")
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return valid_students

    def validate(self, data):
        """
        Process TahunAjaran data and validate unique name.
        """
        # Get or create TahunAjaran
        tahun = data.get('tahunAjaran')
        angkatann = data.get("angkatan")
        try:
            tahun_ajaranobj, created = TahunAjaran.objects.get_or_create(tahunAjaran=tahun)
            data['tahunAjaran_instance'] = tahun_ajaranobj
        except Exception as e:
            raise serializers.ValidationError(f"Error with TahunAjaran: {str(e)}")
        try :
            angkatanObj, created = Angkatan.objects.get_or_create(angkatan=angkatann)
            data["angkatan_instance"] = angkatanObj
        except Exception as e:
            raise serializers.ValidationError(f"Error with Angkatan: {str(e)}")
        return data

    def create(self, validated_data):
        """
        Create a new MataPelajaran with proper handling of relationships.
        """
        # Extract related objects
        tahun_ajaranobj = validated_data.pop('tahunAjaran_instance')
        teacher_user = validated_data.pop('teacher')
        students_users = validated_data.pop('siswa_terdaftar', [])
        angkatan = validated_data.pop('angkatan_instance')
        
        # Create MataPelajaran without relationships first
        matapelajaran = MataPelajaran.objects.create(
            kategoriMatpel=validated_data['kategoriMatpel'],
            nama=validated_data['nama'],
            tahunAjaran=tahun_ajaranobj,
            angkatan = angkatan
        )
        
        # Set the teacher using Django's ORM
        teacher_field = MataPelajaran._meta.get_field('teacher')
        column_name = teacher_field.column
        MataPelajaran.objects.filter(id=matapelajaran.id).update(**{column_name: teacher_user.id})
        
        # Refresh from database
        matapelajaran.refresh_from_db()
        
        # Add students
        for user in students_users:
            try:
                student = Student.objects.get(user_id=user.id)
                matapelajaran.siswa_terdaftar.add(student)
            except Exception as e:
                # Log the error but continue with other students
                print(f"Error adding student {user.id}: {str(e)}")
        
        # Refresh from database again
        matapelajaran.refresh_from_db()
        
        return matapelajaran

    def to_representation(self, instance):
        """
        Customize the output representation.
        """
        representation = super().to_representation(instance)
        
        # Add teacher details
        if instance.teacher:
            representation['teacher'] = {
                'id': instance.teacher.user_id,
                'name': instance.teacher.name,
                'username': instance.teacher.username
            }

        if instance.angkatan:
            representation['angkatan'] = {
                'id': instance.angkatan.id,
                'angkatan': instance.angkatan.angkatan
            }
        
        # Add student details
        representation['siswa_terdaftar'] = []
        for student in instance.siswa_terdaftar.all():
            representation['siswa_terdaftar'].append({
                'id': student.user_id,
                'name': student.name,
                'username': student.username
            })
        
        # Add tahunAjaran details
        if instance.tahunAjaran:
            representation['tahunAjaran'] = {
                'id': instance.tahunAjaran.id,
                'tahun': instance.tahunAjaran.tahunAjaran
            }
        
        # Add status field
        representation['status'] = "Active" if instance.isActive else "Inactive"
        
        return representation

    def update(self, instance, validated_data):
        """
        Update a MataPelajaran with proper handling of relationships.
        """
        # Extract related objects if present
        tahun_ajaran_instance = None
        if 'tahunAjaran_instance' in validated_data:
            tahun_ajaran_instance = validated_data.pop('tahunAjaran_instance')
        if 'angkatan_instance' in validated_data:
            angkatan_instance_lagi = validated_data.pop('angkatan_instance')
        
        teacher_user = validated_data.pop('teacher', None)
        students_users = validated_data.pop('siswa_terdaftar', None)
        # try:
        #     angkatanobj, created = Angkatan.objects.get_or_create(angkatan=angkatan_instance_lagi)
        # except Exception as e:
        #     raise serializers.ValidationError(f"Error mendapatkan TahunAjaran: {str(e)}")
        # Update simple fields
        for i, z in validated_data.items():
            print(f'ini i : {i} kalo ini z : {z}')
            instance.i = z
        if 'kategoriMatpel' in validated_data:
            instance.kategoriMatpel = validated_data["kategoriMatpel"]
        if 'nama' in validated_data:
            instance.nama = validated_data["nama"]
        if 'status' in validated_data:
            if validated_data["status"] == "Active":
                instance.isActive = True
            if validated_data["status"] == "Inactive":
                instance.isActive = False
        if 'kategoriMatpel' in validated_data:
            instance.kategoriMatpel = validated_data["kategoriMatpel"]
        # Update tahunAjaran if provided
        if tahun_ajaran_instance:
            instance.tahunAjaran = tahun_ajaran_instance
        if angkatan_instance_lagi:
            instance.angkatan = angkatan_instance_lagi
        
        # Save the instance with updated fields
        instance.save()
        
        # Update teacher if provided
        if teacher_user:
            teacher_field = MataPelajaran._meta.get_field('teacher')
            column_name = teacher_field.column
            MataPelajaran.objects.filter(id=instance.id).update(**{column_name: teacher_user.id})
            instance.refresh_from_db()
        
        # Update students if provided
        if students_users is not None:  # Check for None to distinguish from empty list
            # Clear existing students
            instance.siswa_terdaftar.clear()
            
            # Add new students
            for user in students_users:
                try:
                    student = Student.objects.get(user_id=user.id)
                    instance.siswa_terdaftar.add(student)
                except Exception as e:
                    # Log the error but continue with other students
                    print(f"Error adding student {user.id}: {str(e)}")
        
        # Refresh from database
        instance.refresh_from_db()
        
        return instance
