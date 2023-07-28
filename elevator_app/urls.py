from django.urls import path, re_path
from .views import (
    ElevatorSystemInstanceView,
    ElevatorSystemsView,
    MoveElevator,
    CallElevator,
    SelectFloorView,
    ElevatorReqModelVS,
    ElevatorStationVS,
    MarkStationUnderMaintenanceView,
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
        "initiate-elevator-system",
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
        SelectFloorView.as_view(),
        name="select_floor",
    ),
    path(
        "elevator-request/<int:pk>",
        ElevatorReqModelVS.as_view(actions={"get": "retrieve"}),
        name="elevator_request",
    ),
    path(
        "elevator-station/<int:pk>",
        ElevatorStationVS.as_view(actions={"get": "retrieve"}),
        name="elevator_station",
    ),
    re_path(
        r"mark-station-under-maintenance/(?P<pk>[0-9]+)/(?P<floor_no>[0-9]+)/(?P<flag>(true|false).)",
        MarkStationUnderMaintenanceView.as_view(),
        name="mark_station_under_maintenance",
    ),
]
