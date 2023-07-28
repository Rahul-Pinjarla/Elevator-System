from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.generics import ListCreateAPIView, GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import (
    ElevatorSystemIntanceSerializer,
    MiniElevatorSystemSerializer,
    ElevatorRequestIntanceSerializer,
)
from .models import ElevatorSystem, ElevatorRequest, ElevatorStation
from .elevator_logic import ElevatorLogic


class GetElevatorSystemInstanceMixin(RetrieveModelMixin):
    queryset = ElevatorSystem.objects.all()
    serializer_class = ElevatorSystemIntanceSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(request):
        elevator_system = get_object_or_404(
            ElevatorSystem, pk=request.kwargs.get("pk", None)
        )
        return elevator_system

    def get_serializer(self, instance):
        return self.serializer_class(instance)


class GetElevatorSystemListMixin(ListModelMixin):
    queryset = ElevatorSystem.objects.all()
    serializer_class = MiniElevatorSystemSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ElevatorSystemInstanceView(GetElevatorSystemInstanceMixin, GenericAPIView):
    queryset = ElevatorSystem.objects.all()
    serializer_class = ElevatorSystemIntanceSerializer


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
                    "message": "There are not requests to move the elevator, Use call or select elevators and try again!",
                    "Elevator Current State": data,
                }
            )
        reached_station = (
            next_stop.to_station if next_stop.to_station else next_stop.station_no
        )
        served_reqs = ElevatorRequest.objects.filter(
            to_station=reached_station, served_on=None
        ).all()
        for req in served_reqs:
            req.served_on = timezone.now()
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
        if curr_station.floor_no == from_floor_no:
            data = ElevatorSystemIntanceSerializer(elevator_system).data
            return Response(
                {
                    "message": f"Elevator is already on the floor #{curr_station.floor_no}! You can select the destionation floor now!",
                    "Elevator Current State": data,
                }
            )
        from_station = stations.filter(floor_no=from_floor_no).first()
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


class SelectFloor(APIView, GetElevatorSystemInstanceMixin):
    def patch(self, request, pk, to_floor_no):
        elevator_system = get_object_or_404(ElevatorSystem, pk=pk)
        curr_station = elevator_system.curr_station
        stations = ElevatorStation.objects.filter(elevator_system=elevator_system).all()
        to_station = stations.filter(floor_no=to_floor_no).first()
        if curr_station.floor_no == to_floor_no:
            data = ElevatorSystemIntanceSerializer(elevator_system).data
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


class ElevatorRequestInstanceView(ReadOnlyModelViewSet):
    def retrieve(self, request, pk=None):
        elevator_req = get_object_or_404(ElevatorRequest, pk=pk)
        data = ElevatorRequestIntanceSerializer(elevator_req).data
        return Response(data)
