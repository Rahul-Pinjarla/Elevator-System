from django.urls import path, re_path
from .views import (
    ElevatorSystemInstanceView,
    ElevatorSystemsView,
    MoveElevator,
    CallElevator,
    SelectFloor,
    ElevatorRequestInstanceView,
)

urlpatterns = [
    path(
        "elevator-system/<int:pk>",
        ElevatorSystemInstanceView.as_view(),
        name="elevator_system",
    ),
    path(
        "elevator-systems",
        ElevatorSystemsView.as_view(),
        name="elevator_systems",
    ),
    path(
        "initialise-elevator-system",
        ElevatorSystemsView.as_view(),
        name="inititate_elevator_system",
    ),
    path("move-elevator/<int:pk>", MoveElevator.as_view(), name="move_elevator"),
    path(
        "call-elevator/<int:pk>/<int:from_floor_no>",
        CallElevator.as_view(),
        name="call_elevator",
    ),
    path(
        "select-floor/<int:pk>/<int:to_floor_no>",
        SelectFloor.as_view(),
        name="select_floor",
    ),
    path(
        "elevator-request/<int:pk>",
        ElevatorRequestInstanceView.as_view(actions={"get": "retrieve"}),
        name="elevator_request",
    ),
]
