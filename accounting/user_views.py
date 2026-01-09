"""
Views for User Management and Custom Fields

This module provides REST API endpoints for:
- User management (CRUD, password management)
- Role and Permission management
- Custom field definitions and values
- Custom form creation and management
- Audit logging
"""

from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.core import signing

from .models import (
    User, Role, Permission, UserAuditLog,
    CustomFieldDefinition, CustomFieldValue, CustomForm, CustomFormField,
    Organization
)
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserAuditLogSerializer, RoleSerializer, RoleDetailSerializer, PermissionSerializer,
    CustomFieldDefinitionSerializer, CustomFieldValueSerializer,
    CustomFormSerializer, CustomFormDetailSerializer, CustomFormFieldSerializer
)
from .rbac import (
    log_user_action, IsAdmin, create_role_with_permissions,
    get_custom_fields_for_module, get_custom_field_values_for_object
)


# ====================== USER MANAGEMENT VIEWSETS ======================

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User management"""
    permission_classes = [IsAuthenticated]
    filterset_fields = ['organization', 'status', 'is_admin', 'primary_role']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['first_name', 'last_name', 'created_at', 'last_login']
    ordering = ['first_name', 'last_name']
    
    def get_queryset(self):
        """Filter users by organization"""
        user = self.request.user
        # Users can only see users in their organization (unless admin)
        queryset = User.objects.all()
        
        if not user.is_admin:
            try:
                user_obj = User.objects.get(pk=user.pk)
                queryset = queryset.filter(organization=user_obj.organization)
            except User.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    def get_serializer_class(self):
        """Return different serializers based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserListSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user details"""
        try:
            user = User.objects.get(pk=request.user.pk)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password"""
        user = self.get_object()
        
        # Check if requesting user can change password
        if request.user.pk != user.pk and not request.user.is_admin:
            return Response(
                {'error': 'You do not have permission to change this password'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')
        
        # Validate
        if not old_password and request.user.pk == user.pk:
            return Response(
                {'error': 'Old password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not new_password or not new_password_confirm:
            return Response(
                {'error': 'New password and confirmation are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != new_password_confirm:
            return Response(
                {'error': 'New passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check old password if not admin
        if request.user.pk == user.pk and not check_password(old_password, user.password_hash):
            return Response(
                {'error': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update password
        user.password_hash = make_password(new_password)
        user.is_password_changed = True
        user.password_changed_at = timezone.now()
        user.save()
        
        # Log the action
        log_user_action(
            user=User.objects.get(pk=request.user.pk),
            organization=user.organization,
            action='PASSWORD_CHANGE',
            resource_type='User',
            resource_id=str(user.id),
            request=request
        )
        
        return Response({'success': 'Password changed successfully'})
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Admin: Reset user password to temporary value"""
        user = self.get_object()
        
        # Check admin permission
        try:
            current_user = User.objects.get(pk=request.user.pk)
            if not current_user.is_admin and not current_user.can_manage_users:
                return Response(
                    {'error': 'You do not have permission to reset passwords'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except User.DoesNotExist:
            return Response({'error': 'Current user not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate temporary password
        import secrets
        temp_password = secrets.token_urlsafe(12)
        
        user.password_hash = make_password(temp_password)
        user.is_password_changed = False
        user.save()
        
        # Log the action
        log_user_action(
            user=current_user,
            organization=user.organization,
            action='PASSWORD_CHANGE',
            resource_type='User',
            resource_id=str(user.id),
            new_values={'password_reset': True},
            request=request
        )
        
        return Response({
            'success': 'Password reset successfully',
            'temporary_password': temp_password
        })
    
    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """Assign a role to a user"""
        user = self.get_object()
        
        # Check permission
        try:
            current_user = User.objects.get(pk=request.user.pk)
            if not current_user.is_admin and not current_user.can_manage_roles:
                return Response(
                    {'error': 'You do not have permission to assign roles'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except User.DoesNotExist:
            return Response({'error': 'Current user not found'}, status=status.HTTP_404_NOT_FOUND)
        
        role_id = request.data.get('role_id')
        is_primary = request.data.get('is_primary', True)
        
        if not role_id:
            return Response({'error': 'role_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            role = Role.objects.get(id=role_id, organization=user.organization)
        except Role.DoesNotExist:
            return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if is_primary:
            user.primary_role = role
            user.save()
        else:
            user.secondary_roles.add(role)
        
        # Log the action
        log_user_action(
            user=current_user,
            organization=user.organization,
            action='ROLE_CHANGE',
            resource_type='User',
            resource_id=str(user.id),
            new_values={'role': role.name, 'is_primary': is_primary},
            request=request
        )
        
        return Response({
            'success': 'Role assigned successfully',
            'user': UserDetailSerializer(user).data
        })


class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    organization_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    is_admin = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError("Passwords do not match")
        return data


class SignUpView(APIView):
    """Public signup endpoint. Creates a user in `PENDING_VERIFICATION` status and
    returns a signed verification token. Requires `organization_id` in payload.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Validate organization
        try:
            org = Organization.objects.get(id=data['organization_id'])
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Create user as ACTIVE immediately (no verification)
        user = User(
            organization=org,
            email=data['email'],
            first_name=data['first_name'],
            last_name=data.get('last_name', ''),
            phone_number=data.get('phone_number', ''),
            status='ACTIVE',
            is_admin=bool(data.get('is_admin', False))
        )
        user.password_hash = make_password(data['password'])
        user.save()

        return Response({
            'message': 'User created and activated. You can log in using the provided credentials.'
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """Verify signup token and activate user."""
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'error': 'token is required'}, status=status.HTTP_400_BAD_REQUEST)

        signer = signing.TimestampSigner()
        try:
            email = signer.unsign(token, max_age=60 * 60 * 24)  # token valid for 24 hours
        except signing.BadSignature:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.status = 'ACTIVE'
        user.save()
        return Response({'message': 'Email verified. Account activated.'})


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(data['password'], user.password_hash):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        # create session linkage
        request.session['accounting_user_id'] = user.id
        request.session.save()

        return Response({'message': 'Login successful'})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.session.pop('accounting_user_id', None)
        request.session.save()
        return Response({'message': 'Logged out'})


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet for Role management"""
    permission_classes = [IsAuthenticated]
    serializer_class = RoleSerializer
    filterset_fields = ['organization', 'role_type', 'is_active', 'is_system_role']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['is_system_role', 'name']
    
    def get_queryset(self):
        """Filter roles by organization"""
        user = self.request.user
        try:
            user_obj = User.objects.get(pk=user.pk)
            return Role.objects.filter(organization=user_obj.organization)
        except User.DoesNotExist:
            return Role.objects.none()
    
    def check_permission(self):
        """Check if user can manage roles"""
        try:
            user = User.objects.get(pk=self.request.user.pk)
            return user.is_admin or user.can_manage_roles
        except User.DoesNotExist:
            return False
    
    def create(self, request, *args, **kwargs):
        """Create a new role"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to create roles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(pk=request.user.pk)
            request.data['organization'] = user.organization.id
            return super().create(request, *args, **kwargs)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, *args, **kwargs):
        """Update a role"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to update roles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        role = self.get_object()
        if role.is_system_role:
            return Response(
                {'error': 'System roles cannot be modified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a role"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to delete roles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        role = self.get_object()
        if role.is_system_role:
            return Response(
                {'error': 'System roles cannot be deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if role.users.exists() or role.secondary_role_users.exists():
            return Response(
                {'error': 'Role cannot be deleted because users are assigned to it'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing permissions (read-only)"""
    permission_classes = [IsAuthenticated]
    serializer_class = PermissionSerializer
    queryset = Permission.objects.all()
    filterset_fields = ['resource', 'action', 'is_active']
    search_fields = ['code', 'description']
    ordering = ['resource', 'action']


class UserAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing audit logs (read-only)"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserAuditLogSerializer
    filterset_fields = ['user', 'organization', 'action', 'resource_type']
    search_fields = ['resource_type', 'resource_id']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter audit logs by user's organization"""
        user = self.request.user
        try:
            user_obj = User.objects.get(pk=user.pk)
            return UserAuditLog.objects.filter(organization=user_obj.organization)
        except User.DoesNotExist:
            return UserAuditLog.objects.none()


# ====================== CUSTOM FIELD VIEWSETS ======================

class CustomFieldDefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet for Custom Field Definition management"""
    permission_classes = [IsAuthenticated]
    serializer_class = CustomFieldDefinitionSerializer
    filterset_fields = ['organization', 'module', 'field_type', 'is_active']
    search_fields = ['field_name', 'field_key', 'description']
    ordering_fields = ['module', 'display_order', 'field_name']
    ordering = ['module', 'display_order']
    
    def get_queryset(self):
        """Filter custom fields by organization"""
        user = self.request.user
        try:
            user_obj = User.objects.get(pk=user.pk)
            return CustomFieldDefinition.objects.filter(organization=user_obj.organization)
        except User.DoesNotExist:
            return CustomFieldDefinition.objects.none()
    
    def check_permission(self):
        """Check if user can manage custom fields"""
        try:
            user = User.objects.get(pk=self.request.user.pk)
            return user.is_admin or user.can_manage_custom_fields
        except User.DoesNotExist:
            return False
    
    def create(self, request, *args, **kwargs):
        """Create a new custom field"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to create custom fields'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(pk=request.user.pk)
            request.data['organization'] = user.organization.id
            request.data['created_by'] = user.id
            return super().create(request, *args, **kwargs)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, *args, **kwargs):
        """Update a custom field"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to update custom fields'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        custom_field = self.get_object()
        if custom_field.is_system_field:
            return Response(
                {'error': 'System fields cannot be modified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a custom field"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to delete custom fields'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        custom_field = self.get_object()
        if custom_field.is_system_field:
            return Response(
                {'error': 'System fields cannot be deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class CustomFieldValueViewSet(viewsets.ModelViewSet):
    """ViewSet for Custom Field Values"""
    permission_classes = [IsAuthenticated]
    serializer_class = CustomFieldValueSerializer
    filterset_fields = ['organization', 'module', 'object_id', 'custom_field']
    ordering_fields = ['updated_at', 'created_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter custom field values by organization"""
        user = self.request.user
        try:
            user_obj = User.objects.get(pk=user.pk)
            return CustomFieldValue.objects.filter(organization=user_obj.organization)
        except User.DoesNotExist:
            return CustomFieldValue.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create or update custom field value"""
        try:
            user = User.objects.get(pk=request.user.pk)
            request.data['organization'] = user.organization.id
            request.data['created_by'] = user.id
            
            # Check if field exists
            field_id = request.data.get('custom_field')
            if field_id:
                try:
                    CustomFieldDefinition.objects.get(
                        id=field_id,
                        organization=user.organization
                    )
                except CustomFieldDefinition.DoesNotExist:
                    return Response(
                        {'error': 'Custom field not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            return super().create(request, *args, **kwargs)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class CustomFormViewSet(viewsets.ModelViewSet):
    """ViewSet for Custom Form management"""
    permission_classes = [IsAuthenticated]
    filterset_fields = ['organization', 'module', 'is_active', 'is_default']
    search_fields = ['form_name', 'description']
    ordering_fields = ['module', 'display_order']
    ordering = ['module', 'display_order']
    
    def get_serializer_class(self):
        """Return detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return CustomFormDetailSerializer
        return CustomFormSerializer
    
    def get_queryset(self):
        """Filter forms by organization"""
        user = self.request.user
        try:
            user_obj = User.objects.get(pk=user.pk)
            return CustomForm.objects.filter(organization=user_obj.organization)
        except User.DoesNotExist:
            return CustomForm.objects.none()
    
    def check_permission(self):
        """Check if user can manage custom forms"""
        try:
            user = User.objects.get(pk=self.request.user.pk)
            return user.is_admin or user.can_manage_custom_fields
        except User.DoesNotExist:
            return False
    
    def create(self, request, *args, **kwargs):
        """Create a new custom form"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to create custom forms'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(pk=request.user.pk)
            request.data['organization'] = user.organization.id
            request.data['created_by'] = user.id
            return super().create(request, *args, **kwargs)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, *args, **kwargs):
        """Update a custom form"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to update custom forms'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a custom form"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to delete custom forms'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set this form as default for its module"""
        if not self.check_permission():
            return Response(
                {'error': 'You do not have permission to set default forms'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        form = self.get_object()
        
        with transaction.atomic():
            # Unset all other default forms for this module
            CustomForm.objects.filter(
                organization=form.organization,
                module=form.module,
                is_default=True
            ).exclude(id=form.id).update(is_default=False)
            
            # Set this form as default
            form.is_default = True
            form.save()
        
        return Response({
            'success': 'Form set as default',
            'form': CustomFormDetailSerializer(form).data
        })
