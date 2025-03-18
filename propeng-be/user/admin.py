from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.contrib.admin.sites import AdminSite
from .models import User, Student, Teacher
from kelas.models import Kelas
from matapelajaran.models import MataPelajaran
from django import forms
from rest_framework import serializers
from user.models import DeploymentInfo

class SuperuserAdminSite(AdminSite):
    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser

admin_site = SuperuserAdminSite(name='admin')

class CustomUserAdminForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[('admin', 'Admin')], initial='admin')
    
    class Meta:
        model = User
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data)
        # Always set role to admin
        cleaned_data['role'] = 'admin'
        return cleaned_data

class CustomUserAdmin(UserAdmin):
    form = CustomUserAdminForm
    model = User
    list_display = ('username', 'role', 'is_staff', 'is_active')
    role = 'admin'
    # Include custom fields in the admin form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Role Information', {'fields': ('role',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'role', 'is_active')}
        ),
    )
    
    # Filter to show only admin users
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(role='admin')
    
    # Set default role to admin when creating a new user
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial['role'] = 'admin'
        return initial
    
    # Override to force role field to only have 'admin' choice
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'role':
            kwargs['choices'] = [('admin', 'Admin')]
        return super().formfield_for_choice_field(db_field, request, **kwargs)
    
    # Ensure save always sets role to admin
    def save_model(self, request, obj, form, change):
        obj.role = 'admin'
        print(obj)
        print("tutoring here")
        super().save_model(request, obj, form, change)

class CustomTeacherAdminForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[('teacher', 'Teacher')], initial='teacher')
    
    class Meta:
        model = User
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data)
        # Always set role to admin
        cleaned_data['role'] = 'teacher'
        return cleaned_data

class CustomTeacherAdmin(admin.ModelAdmin):
    form = CustomUserAdminForm
    model = User
    list_display = ('name', 'username', 'nisp', 'homeroomId', 'isActive', 'isDeleted')
    # role = 'teacher'
    # Include custom fields in the admin form
    fieldsets = (
        (None, {'fields': ('username','name','nisp')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username','name','nisp')}
        ),
    )
    
    # Filter to show only admin users
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(user__role='teacher')
    
    # Set default role to admin when creating a new user
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        # initial['role'] = 'Teacher'
        return initial
    
    # Override to force role field to only have 'admin' choice
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'role':
            kwargs['choices'] = [('teacher', 'Teacher')]
        return super().formfield_for_choice_field(db_field, request, **kwargs)
    
    # Ensure save always sets role to admin
    def save_model(self, request, obj, form, change):
        print(obj)
        print("tutoring here")
        super().save_model(request, obj, form, change)

class CustomStudentAdminForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[('student', 'Student')], initial='student')
    
    class Meta:
        model = User
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data)
        # Always set role to admin
        cleaned_data['role'] = 'student'
        return cleaned_data
    # test commit
class CustomStudentAdmin(admin.ModelAdmin):
    form = CustomUserAdminForm
    model = User
    list_display = ('name', 'username', 'nisn', 'angkatan', 'isActive', 'isDeleted')
    # role = 'teacher'
    # Include custom fields in the admin form
    fieldsets = (
        (None, {'fields': ('username','name','nisn')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username','name','nisn')}
        ),
    )
    
    # Filter to show only admin users
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(user__role='student')
    
    # Set default role to admin when creating a new user
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        # initial['role'] = 'Teacher'
        return initial
    
    # Override to force role field to only have 'admin' choice
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'role':
            kwargs['choices'] = [('student', 'Student')]
        return super().formfield_for_choice_field(db_field, request, **kwargs)
    
    # Ensure save always sets role to admin
    def save_model(self, request, obj, form, change):
        print(obj)
        print("tutoring here")
        super().save_model(request, obj, form, change)

class DeploymentInfoAdmin(admin.ModelAdmin):
    list_display = ('deployed_at',)


class MataPelajaranAdmin(admin.ModelAdmin):
    list_display = ('nama', 'kategoriMatpel', 'tahunAjaran', 'angkatan', 'teacher', 'isActive')
    list_filter = ('kategoriMatpel', 'tahunAjaran', 'angkatan', 'isActive')
    search_fields = ('nama', 'kode', 'teacher__name')
    readonly_fields = ('kode', 'createdAt', 'updatedAt')
    filter_horizontal = ('siswa_terdaftar',)

    fieldsets = (
        (None, {
            'fields': ('nama', 'kode', 'kategoriMatpel')
        }),
        ('Informasi Akademik', {
            'fields': ('tahunAjaran', 'angkatan', 'teacher')
        }),
        ('Status', {
            'fields': ('isActive', 'isDeleted')
        }),
        ('Siswa', {
            'fields': ('siswa_terdaftar',)
        }),
        ('Timestamps', {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',)
        })
    )
class KelasAdmin(admin.ModelAdmin):
    list_display = ('namaKelas', 'waliKelas', 'tahunAjaran', 'angkatan')
    list_filter = ('tahunAjaran', 'angkatan')
    search_fields = ('namaKelas', 'waliKelas__name')
    filter_horizontal = ('siswa',)

    fieldsets = (
        (None, {
            'fields': ('namaKelas',)
        }),
        ('Informasi Kelas', {
            'fields': ('waliKelas', 'tahunAjaran', 'angkatan')
        }),
        ('Siswa', {
            'fields': ('siswa',)
        })
    )

admin_site.register(Kelas, KelasAdmin)
admin_site.register(MataPelajaran, MataPelajaranAdmin)
admin_site.register(User, CustomUserAdmin)  # Admin users
admin_site.register(Teacher, CustomTeacherAdmin)
admin_site.register(Student, CustomStudentAdmin)
admin_site.register(DeploymentInfo, DeploymentInfoAdmin)
# # Register Student and Teacher models
# admin_site.register(Student, StudentAdmin)
# admin_site.register(Teacher, TeacherAdmin)
admin.site = admin_site