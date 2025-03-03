from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from .models import User, Student, Teacher

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('role', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    # Custom function to create a new user with role-specific attributes
    def create_user(self, request, queryset):
        for user_data in queryset:
            username = user_data.get("username")
            email = user_data.get("email")
            password = user_data.get("password")
            role = user_data.get("role")
            nomorinduk = user_data.get("nomorinduk")  # NISN for students, NISP for teachers

            user = User.objects.create(
                username=username,
                email=email,
                role=role,
                password=make_password(password)  # Hash password before saving
            )

            # Create Student or Teacher based on role
            if role == "student":
                Student.objects.create(user=user, nisn=nomorinduk)
            elif role == "teacher":
                Teacher.objects.create(user=user, nisp=nomorinduk)

            user.save()

    actions = ["create_user"]

admin.site.register(User, CustomUserAdmin)
admin.site.register(Student)
admin.site.register(Teacher)
