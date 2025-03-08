from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Student, Teacher, TahunAjaran
from django.contrib.auth import get_user_model

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email  # Adds email to JWT payload
        return token
    
class UserSerializer(serializers.ModelSerializer):
    nomorinduk = serializers.CharField(write_only=True)  # Custom field for NISN/NISP
    tahunAjaran = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'nomorinduk', 'tahunAjaran']
        extra_kwargs = {'password': {'write_only': True}}  # Hide password in responses
    
    

    def create(self, validated_data):
        role = validated_data.pop('role')
        nomorinduk = validated_data.pop('nomorinduk', None) if role == "student" else None
        tahunAjaran = validated_data.pop("tahunAjaran", None) if role == "student" else None

        # Create base User
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            role=role,
            password=make_password(validated_data['password'])  # Hash password
        )
        print("disini serializer" + user.username + user.email + user.role)
        print(validated_data)

        # Assign role-specific attributes
        if role == "student":
            if tahunAjaran is None or tahunAjaran<=0 or tahunAjaran is str:
                user.delete()
                raise serializers.ValidationError({"tahunAjaran is incorrect, either negative or in string"})
            # Buat atau ambil instance TahunAjaran
            tahun_ajaran_instance, created = TahunAjaran.objects.get_or_create(tahunAjaran=tahunAjaran)

            # Buat Student dengan instance TahunAjaran
            Student.objects.create(user=user, nisn=nomorinduk, tahunAjaran=tahun_ajaran_instance)

        elif role == "teacher":
            Teacher.objects.create(user=user, nisp=nomorinduk)

        return user
