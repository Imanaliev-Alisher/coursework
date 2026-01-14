from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Разрешение на чтение для всех аутентифицированных пользователей.
    Разрешение на изменение только для администраторов.
    """

    def has_permission(self, request, view):
        # Разрешить чтение для всех аутентифицированных пользователей
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Разрешить изменение только администраторам
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsAdminOrOwner(BasePermission):
    """
    Разрешение на изменение только для администраторов или владельца объекта.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_staff:
            return True
        
        # Владелец может просматривать и изменять свои данные
        if hasattr(obj, 'id'):
            return obj.id == request.user.id
        
        return False


class IsAdmin(BasePermission):
    """
    Разрешение только для администраторов.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff
