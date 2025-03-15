from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.contrib.admin.sites import AdminSite
from .models import User, Student, Teacher
from django import forms

# Custom admin site that only allows superusers
class SuperuserAdminSite(AdminSite):
    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser

# Create custom admin site instance
admin_site = SuperuserAdminSite(name='admin')

# Custom form for User model that limits role choices to 'admin' only
class CustomUserAdminForm(forms.ModelForm):
    # Define role field explicitly with only admin option
    ADMIN_ONLY_CHOICES = [('admin', 'Admin')]
    role = forms.ChoiceField(choices=ADMIN_ONLY_CHOICES, required=True)
    
    class Meta:
        model = User
        fields = '__all__'
    
    # Override the constructor to ensure the role field is always limited
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hard-code role choices to only 'admin'
        self.fields['role'].choices = self.ADMIN_ONLY_CHOICES
        
        # If editing an existing user and role isn't admin, force it to admin
        if self.instance and self.instance.pk and self.instance.role != 'admin':
            self.instance.role = 'admin'

class CustomUserAdmin(UserAdmin):
    form = CustomUserAdminForm
    model = User
    list_display = ('username', 'role', 'is_staff', 'is_active')
    
    # Override to force 'admin' role in both add and change forms
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('role', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    # Ensure 'admin' is the only choice for role when saving
    def save_model(self, request, obj, form, change):
        obj.role = 'admin'  # Force role to be admin
        super().save_model(request, obj, form, change)

    # Custom function to create a new user with role-specific attributes
    def create_user(self, request, queryset):
        for user_data in queryset:
            username = user_data.get("username")
            password = user_data.get("password")

            user = User.objects.create(
                username=username,
                email=None,
                role="admin",
                password=make_password(password)  # Hash password before saving
            )
            user.save()

    actions = ["create_user"]

# Register models with the custom admin site
admin_site.register(User, CustomUserAdmin)
# Replace default admin site with custom admin site
admin.site = admin_site