from queue import Full
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
        print("coba disini di token obtain")
        token = super().get_token(user)
        token['email'] = user.email  # Adds email to JWT payload
        # need further discussion on how token reference
        return token
    
class UserSerializer(serializers.ModelSerializer):
    nomorInduk = serializers.CharField(write_only=True)  # Custom field for NISN/NISP
    angkatan = serializers.IntegerField(write_only=True)
    name = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ['name', 'email','username', 'password', 'role', 'nomorInduk', 'angkatan']
        extra_kwargs = {'password': {'write_only': True}}  # Hide password in responses
    

    def create(self, validated_data):
        print(validated_data)
        role = validated_data.pop('role')
        name = validated_data.pop('name')
        nomorInduk = validated_data.pop('nomorInduk', None)
        angkatan = validated_data.pop('angkatan', None)
        try:
            nomorInduk = int(nomorInduk)
        except:
            raise serializers.ValidationError({"status":"400","Message":"User with that Nomor Induk can't be numbers"})

        # remove Existing Email validation 
        # if User.objects.filter(email=validated_data['email']).exists():
        #     raise serializers.ValidationError({"status":"400","Message":"User with that email already exists"})

        # Create base User
        print("masih ke run")
        print(validated_data)
        try:
            user = User.objects.create_user(
                username=validated_data['username'],
                # default, need further discussion
                email=validated_data['username'],
                role=role,
                password=validated_data['password']  # Hash password
            )
        except:
            raise serializers.ValidationError({"status":"400","Message":"User with that username credentials is already here"})
        print("disini serializer" + user.username + user.role)
        print(validated_data)

        # Assign role-specific attributes
        if role == "student":
            if angkatan is None or angkatan<=0 or angkatan is str:
                print("Yes")
                user.delete()
                raise serializers.ValidationError({"status":"400","Message":"tahunAjaran is incorrect, either negative or in string"})
            if Student.objects.filter(nisn=nomorInduk).exists():
                user.delete()
                raise serializers.ValidationError({"status":"400","Message":"Student with that NISN numbers already exist"})
            # Buat atau ambil instance TahunAjaran
            # need further discussion on tahunAjaran field cc: arshad 
            # print("yes too")
            # tahun_ajaran_instance, created = TahunAjaran.objects.get_or_create(angkatan=angkatan)

            # Buat Student dengan instance TahunAjaran
            Student.objects.create(user=user, nisn=nomorInduk, name=name, angkatan=angkatan)

        elif role == "teacher":
            if Teacher.objects.filter(nisp=nomorInduk).exists():
                user.delete()
                raise serializers.ValidationError({"status":"400","Message":"Teacher with that NISP numbers already exist"})
            Teacher.objects.create(user=user, nisp=nomorInduk, username=user.username, name=name, angkatan=angkatan)
            
        return user

