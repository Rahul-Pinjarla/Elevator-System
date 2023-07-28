from django.db import models
import enum


@enum.unique
class Directions(str, enum.Enum):
    UP = "UP"
    DOWN = "DOWN"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class TimeStampBaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ElevatorSystem(TimeStampBaseModel):
    stations_count = models.PositiveIntegerField()
    curr_station = models.ForeignKey(
        "ElevatorStation", on_delete=models.DO_NOTHING, null=True, blank=True
    )
    curr_direction = models.CharField(
        max_length=50, choices=Directions.choices(), default=Directions.UP
    )
    building_name = models.CharField(max_length=100, default="Name Unkown")

    def get_pending_requests(self):
        nearest_floor_no_case = models.Case(
            models.When(to_station=None, then="from_station__under_maintenance_since"),
            default="to_station__under_maintenance_since",
        )
        return ElevatorRequest.objects.annotate(
            nearest_floor_um=nearest_floor_no_case
        ).filter(elevator_system=self, served_on=None, nearest_floor_um=None)


class ElevatorStation(TimeStampBaseModel):
    elevator_system = models.ForeignKey(ElevatorSystem, on_delete=models.CASCADE)
    floor_no = models.PositiveIntegerField()
    under_maintenance_since = models.DateTimeField(default=None, blank=True, null=True)


class ElevatorRequest(TimeStampBaseModel):
    elevator_system = models.ForeignKey(ElevatorSystem, on_delete=models.CASCADE)
    from_station = models.ForeignKey(
        ElevatorStation, on_delete=models.CASCADE, related_name="from_station"
    )
    to_station = models.ForeignKey(
        ElevatorStation,
        on_delete=models.CASCADE,
        related_name="to_station",
        null=True,
        blank=True,
    )
    served_on = models.DateTimeField(blank=True, null=True, default=None)
    skip_count = models.PositiveIntegerField(default=0)

    def record_skipped(self, *args, **kwargs):
        self.skip_count = self.skip_count + 1
        self.save()
