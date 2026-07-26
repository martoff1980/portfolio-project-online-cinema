from src.models.auth import User, UserGroupEnum
from src.models.orders import Order, OrderStatusEnum


class OrderService:
    """
    Business logic service for order management and rights verification.
    """

    @staticmethod
    def can_cancel_any_order(user: User) -> bool:
        """
        RBAC permission check: can the user cancel any order?
        (rules ADMIN/MODERATOR).
        """
        if not user or not user.group:
            return False
        return user.group.name in [
            UserGroupEnum.ADMIN, UserGroupEnum.MODERATOR
        ]

    @staticmethod
    def validate_status_transition(
        order: Order,
        target_status: OrderStatusEnum
    ) -> None:
        """
        Business rule: validation of the transition between order statuses.
        """
        if (
            order.status == OrderStatusEnum.PAID and
            target_status == OrderStatusEnum.PAID
        ):
            raise ValueError("Order is already paid")

        if order.status == OrderStatusEnum.CANCELED:
            raise ValueError("Cannot change status of a cancelled order")
