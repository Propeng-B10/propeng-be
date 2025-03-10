from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Student, Teacher, TahunAjaran
from django.contrib.auth import get_user_model
import re
from django.contrib.auth.hashers import make_password


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['new_password']

    def validate_new_password(self, value):
        """Validate the new password for strength."""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")

        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")

        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")

        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one number")

        return value

    def update(self, instance, validated_data):
        instance.password = make_password(validated_data['new_password'])  # Hash new password
        instance.save()
        return instance

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email  # Adds email to JWT payload
        return token
    
class UserSerializer(serializers.ModelSerializer):
    nomorinduk = serializers.CharField(write_only=True)  # Custom field for NISN/NISP
    tahunAjaran = serializers.IntegerField(write_only=True, required=False)
    name = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'password', 'role', 'nomorinduk', 'tahunAjaran']
        extra_kwargs = {'password': {'write_only': True}}  # Hide password in responses
    

    def create(self, validated_data):
        print(validated_data)
        role = validated_data.pop('role')
        name = validated_data.pop('name')
        nomorinduk = validated_data.pop('nomorinduk', None)
        tahunAjaran = validated_data.pop('tahunAjaran', None) if role == "student" else None
        try:
            nomorinduk = int(nomorinduk)
        except:
            raise serializers.ValidationError({"status":"400","Message":"User with that nomor induk can't be numbers"})

        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError({"status":"400","Message":"User with that email already exists"})

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
                print("Yes")
                user.delete()
                raise serializers.ValidationError({"status":"400","Message":"tahunAjaran is incorrect, either negative or in string"})
            if Student.objects.filter(nisn=nomorinduk).exists():
                user.delete()
                raise serializers.ValidationError({"status":"400","Message":"Student with that NISN numbers already exist"})
            # Buat atau ambil instance TahunAjaran
            print("yes too")
            tahun_ajaran_instance, created = TahunAjaran.objects.get_or_create(tahunAjaran=tahunAjaran)

            # Buat Student dengan instance TahunAjaran
            Student.objects.create(user=user, nisn=nomorinduk, name=name, tahunAjaran=tahun_ajaran_instance)

        elif role == "teacher":
            if Teacher.objects.filter(nisp=nomorinduk).exists():
                user.delete()
                raise serializers.ValidationError({"status":"400","Message":"Teacher with that NISP numbers already exist"})
            Teacher.objects.create(user=user, nisp=nomorinduk, username=user.username, name=name)
            
        return user

