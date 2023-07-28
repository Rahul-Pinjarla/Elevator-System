from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import (
    ElevatorSystemIntanceSerializer,
    MiniElevatorSystemSerializer,
    ElevatorRequestIntanceSerializer,
    ElevatorStationDetailSerializer,
)
from .models import ElevatorSystem, ElevatorRequest, ElevatorStation
from .elevator_logic import ElevatorLogic


class RetrieveIsGetMixin:
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class GetElevatorSystemInstanceMixin(RetrieveModelMixin, RetrieveIsGetMixin):
    queryset = ElevatorSystem.objects.all()
    serializer_class = ElevatorSystemIntanceSerializer

    def get_object(request):
        elevator_system = get_object_or_404(
            ElevatorSystem, pk=request.kwargs.get("pk", None)
        )
        return elevator_system

    def get_serializer(self, instance):
        return self.serializer_class(instance)


class GetElevatorSystemListMixin(ListModelMixin, RetrieveIsGetMixin):
    queryset = ElevatorSystem.objects.all()
    serializer_class = MiniElevatorSystemSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ElevatorSystemInstanceView(GetElevatorSystemInstanceMixin, GenericAPIView):
    pass


class ElevatorReqModelVS(ReadOnlyModelViewSet):
    queryset = ElevatorRequest.objects.all()
    serializer_class = ElevatorRequestIntanceSerializer


class ElevatorSystemsView(GetElevatorSystemListMixin, GenericAPIView):
    def post(self, request, *args, **kwargs):
        elevator_system_serializer = ElevatorSystemIntanceSerializer(data=request.data)
        if not elevator_system_serializer.is_valid(raise_exception=True):
            return Response({"Error": "Some Error Occured, Please try again!"})
        new_elevator_system = elevator_system_serializer.save()
        first_station = None
        for i in range(elevator_system_serializer.data.get("stations_count", 0)):
            new_elevator_station = ElevatorStation(
                floor_no=i + 1, elevator_system=new_elevator_system
            )
            new_elevator_station.save()
            if not first_station:
                first_station = new_elevator_station
        new_elevator_system.curr_station = first_station
        new_elevator_system.save()
        return Response(
            {
                "message": "New Elevator System created successfully!!",
                "new_elevator_system": elevator_system_serializer.data,
            }
        )


class MoveElevator(APIView, GetElevatorSystemInstanceMixin):
    def patch(self, request, pk):
        elevator_system = get_object_or_404(ElevatorSystem, pk=pk)
        next_stop, direction = ElevatorLogic.get_next_request(elevator_system)
        if next_stop is None:
            data = ElevatorSystemIntanceSerializer(elevator_system).data
            return Response(
                {
                    "message": "There are no requests to move the elevator, Use call or select elevators and try again!",
                    "Elevator Current State": data,
                }
            )
        reached_station = (
            next_stop.to_station if next_stop.to_station else next_stop.from_station
        )
        served_reqs = ElevatorRequest.objects.filter(
            Q(to_station=reached_station)
            | Q(from_station=reached_station) & Q(served_on=None)
        )
        served_reqs.update(served_on=timezone.now())
        for req in served_reqs:
            req.save()
        elevator_system.curr_direction = direction
        elevator_system.curr_station = reached_station
        elevator_system.save()
        data = ElevatorSystemIntanceSerializer(elevator_system).data
        return Response(
            {
                "message": f"Lift moved to floor #{reached_station.floor_no} successfully!",
                "Elevator Current State": data,
            }
        )


class CallElevator(APIView, GetElevatorSystemInstanceMixin):
    def patch(self, request, pk, from_floor_no):
        elevator_system = get_object_or_404(ElevatorSystem, pk=pk)
        curr_station = elevator_system.curr_station
        stations = ElevatorStation.objects.filter(elevator_system=elevator_system).all()
        data = ElevatorSystemIntanceSerializer(elevator_system).data
        if curr_station.floor_no == from_floor_no:
            return Response(
                {
                    "message": f"Elevator is already on the floor #{curr_station.floor_no}! You can select the destionation floor now!",
                    "Elevator Current State": data,
                }
            )
        from_station = stations.filter(floor_no=from_floor_no).first()
        if from_station.under_maintenance_since:
            return Response(
                {
                    "message": f"Sorry! This floor #{curr_station.floor_no} elevator station is under maintenance!",
                    "Elevator Current State": data,
                }
            )
        new_elevator_req = ElevatorRequest(
            from_station=from_station, elevator_system=elevator_system
        )
        new_elevator_req.save()
        data = ElevatorSystemIntanceSerializer(elevator_system).data
        return Response(
            {
                "message": "Elevator call request Saved! Elevator will reach this floor shortly!",
                "Elevator Current State": data,
            }
        )


class SelectFloorView(APIView, GetElevatorSystemInstanceMixin):
    def patch(self, request, pk, to_floor_no):
        elevator_system = get_object_or_404(ElevatorSystem, pk=pk)
        curr_station = elevator_system.curr_station
        stations = ElevatorStation.objects.filter(elevator_system=elevator_system).all()
        to_station = stations.filter(floor_no=to_floor_no).first()
        data = ElevatorSystemIntanceSerializer(elevator_system).data
        if to_station.under_maintenance_since:
            return Response(
                {
                    "message": f"The selected floor #{curr_station.floor_no} station is under maintenance! Please select a different floor!",
                    "Elevator Current State": data,
                }
            )
        if curr_station.floor_no == to_floor_no:
            return Response(
                {
                    "message": f"Elevator is already on the floor #{curr_station.floor_no}! Please select a different floor!",
                    "Elevator Current State": data,
                }
            )
        pending_elevator_req = ElevatorRequest.objects.filter(
            from_station__floor_no=curr_station.floor_no, to_station=None
        ).first()
        if pending_elevator_req:
            pending_elevator_req.to_station = to_station
            pending_elevator_req.save()
        else:
            new_elevator_req = ElevatorRequest(
                from_station=curr_station,
                to_station=to_station,
                elevator_system=elevator_system,
            )
            new_elevator_req.save()
        data = ElevatorSystemIntanceSerializer(elevator_system).data
        return Response(
            {
                "message": "Select Floor request Saved! Elevator will reach the selected floor shortly!",
                "Elevator Current State": data,
            }
        )


class ElevatorStationVS(ReadOnlyModelViewSet):
    """
    Elevator Station Read only view set
    """

    queryset = ElevatorStation.objects.all()
    serializer_class = ElevatorStationDetailSerializer


class MarkStationUnderMaintenanceView(APIView, GetElevatorSystemInstanceMixin):
    def patch(self, request, pk, floor_no, flag):
        elevator_system = get_object_or_404(ElevatorSystem, pk=pk)
        station = ElevatorStation.objects.filter(
            elevator_system=elevator_system, floor_no=floor_no
        ).first()
        if not station:
            data = ElevatorSystemIntanceSerializer(elevator_system).data
            return Response(
                {
                    "message": f"This Elevator System has only {elevator_system.stations_count} stations.",
                    "Elevator Current State": data,
                }
            )
        if flag:
            station.under_maintenance_since = timezone.now()
        else:
            station.under_maintenance_since = None
        station.save()
        data = ElevatorSystemIntanceSerializer(elevator_system).data
        return Response(
            {
                "message": f'Station at floor #{floor_no} is {"marked" if flag else "unmarked"} under maintenance!',
                "Elevator Current State": data,
            }
        )
