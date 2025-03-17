from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.contrib.admin.sites import AdminSite
from .models import User, Student, Teacher
from django import forms
from rest_framework import serializers

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
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role Information', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role','is_staff', 'is_active')}
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
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2')}
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
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2')}
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

admin_site.register(User, CustomUserAdmin)  # Admin users
admin_site.register(Teacher, CustomTeacherAdmin)
admin_site.register(Student, CustomStudentAdmin)
# # Register Student and Teacher models
# admin_site.register(Student, StudentAdmin)
# admin_site.register(Teacher, TeacherAdmin)

admin.site = admin_site