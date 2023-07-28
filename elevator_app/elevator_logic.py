from django.db.models import Case, When
from .models import Directions


class ElevatorLogic:
    @staticmethod
    def _get_next_request_in_direction(pending_req, elevator_system):
        curr_direction = elevator_system.curr_direction
        curr_station = elevator_system.curr_station
        curr_floor_no = curr_station.floor_no
        nearest_floor_no_case = Case(
            When(to_station=None, then="from_station__floor_no"),
            default="to_station__floor_no",
        )
        nearest_req_above = (
            pending_req.annotate(nearest_floor_no=nearest_floor_no_case)
            .filter(nearest_floor_no__gt=curr_floor_no)
            .order_by("nearest_floor_no")
            .first()
        )
        nearest_req_below = (
            pending_req.annotate(nearest_floor_no=nearest_floor_no_case)
            .filter(nearest_floor_no__lt=curr_floor_no)
            .order_by("nearest_floor_no")
            .last()
        )
        if curr_direction == Directions.UP:
            if not nearest_req_above:
                return nearest_req_below, Directions.DOWN
            return nearest_req_above, Directions.UP
        else:
            if not nearest_req_below:
                return nearest_req_above, Directions.UP
            return nearest_req_below, Directions.DOWN

    @staticmethod
    def get_next_request(elevator_system):
        if not elevator_system.curr_station:
            return None, elevator_system.curr_direction
        pending_reqs = elevator_system.get_pending_requests()
        next_req, direction = ElevatorLogic._get_next_request_in_direction(
            pending_reqs, elevator_system
        )
        return next_req, direction
