from django.urls import reverse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from .models import ElevatorSystem, ElevatorRequest, ElevatorStation
from .elevator_logic import ElevatorLogic

ExtraElevatorReqFields = ("destination", "url")

ElevatorSytemFields = (
    "id",
    "building_name",
    "stations_count",
    "created",
)


class ElevatorStationSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return reverse("elevator_request", kwargs={"pk": obj.id})

    class Meta:
        model = ElevatorStation
        fields = ("id", "floor_no", "url")


def deduce_destination(elevator_req):
    if elevator_req.to_station:
        return elevator_req.to_station
    return elevator_req.from_station


class BaseElevatorRequestModelSerializer(serializers.ModelSerializer):
    from_station = ElevatorStationSerializer()
    to_station = ElevatorStationSerializer()
    destination = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_destination(self, obj):
        return deduce_destination(obj).floor_no

    def get_url(self, obj):
        return reverse("elevator_request", kwargs={"pk": obj.id})


class MiniElevatorRequestSerializer(BaseElevatorRequestModelSerializer):
    """
    This serializers returns the important stuff of elevator request
    """

    class Meta:
        model = ElevatorRequest
        fields = ("id", "from_station", "created", "served_on", *ExtraElevatorReqFields)


class ElevatorRequestIntanceSerializer(BaseElevatorRequestModelSerializer):
    """
    A simple serializer for `ElevatorRequest` model
    """

    class Meta:
        model = ElevatorRequest
        fields = (
            "id",
            "from_station",
            "to_station",
            "served_on",
            "updated",
            "created",
            "skip_count",
            "elevator_system",
            *ExtraElevatorReqFields,
        )


class PendingRequestSerializer(BaseElevatorRequestModelSerializer):
    """
    A simple serializer for pending `ElevatorRequest`s
    this serializer includes the requests destination
    """

    class Meta:
        model = ElevatorRequest
        fields = ("id", "skip_count", "destination")


class BaseElevatorSystemSerializer(serializers.ModelSerializer):
    curr_station = ElevatorStationSerializer(read_only=True)
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return reverse("elevator_system", kwargs={"pk": obj.id})


class MiniElevatorSystemSerializer(BaseElevatorSystemSerializer):
    """
    A serializer for `ElevatorSystem` model.
    Useful for listing all elevator systems.
    And also for new elevator system initiation.
    """

    class Meta:
        model = ElevatorSystem
        read_only_fields = ("curr_station", "curr_direction")
        fields = (*ElevatorSytemFields, "url")


class ElevatorSystemIntanceSerializer(BaseElevatorSystemSerializer):
    """
    A simple serializer for `ElevatorSystem` model.
    Also adds requests into the result payload.
    """

    all_requests = MiniElevatorRequestSerializer(
        source="elevatorrequest_set", many=True, read_only=True
    )

    nextstation = serializers.SerializerMethodField()
    pendingrequests = serializers.SerializerMethodField()

    def get_nextstation(self, obj):
        next_stop, direction = ElevatorLogic.get_next_request(obj)
        obj.curr_direction = direction
        obj.save()
        if next_stop is None:
            return "To Be Decided"
        next_station = (
            next_stop.to_station if next_stop.to_station else next_stop.from_station
        )
        return next_station.floor_no

    def get_pendingrequests(self, obj):
        return PendingRequestSerializer(obj.get_pending_requests(), many=True).data

    class Meta:
        model = ElevatorSystem
        read_only_fields = ("curr_station", "curr_direction")
        fields = (
            *ElevatorSytemFields,
            "stations_count",
            "updated",
            "curr_station",
            "curr_direction",
            "nextstation",
            "pendingrequests",
            "all_requests",
        )
