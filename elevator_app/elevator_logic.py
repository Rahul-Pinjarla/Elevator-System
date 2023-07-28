from django.db.models import Q, Case, When
from .models import Directions


class ElevatorLogic:
    @staticmethod
    def _decide_direction(pending_reqs, elevator_system):
        curr_floor_no = elevator_system.curr_station.floor_no
        if curr_floor_no == 1:
            return Directions.UP
        if curr_floor_no == elevator_system.stations_count:
            return Directions.DOWN
        req_from_above = pending_reqs.filter(
            from_station__floor_no__gt=curr_floor_no
        ).exists()
        req_from_below = pending_reqs.filter(
            from_station__floor_no__lt=curr_floor_no
        ).exists()
        if not req_from_above and not req_from_below:
            return None
        if not req_from_below:
            return Directions.UP
        if not req_from_above:
            return Directions.DOWN
        distance_above = elevator_system.stations_count - curr_floor_no
        distance_below = curr_floor_no - 1
        if distance_above < distance_below:
            direction = Directions.UP
        else:
            direction = Directions.DOWN
        return direction

    @staticmethod
    def _get_high_priority_req(pending_reqs, elevator_system):
        curr_floor_no = elevator_system.curr_station.floor_no
        high_priority_req = (
            pending_reqs.filter(skip_count__gte=3).order_by("created").first()
        )
        if not high_priority_req:
            return False, None
        direction = Directions.DOWN
        if high_priority_req.from_station.floor_no > curr_floor_no:
            direction = Directions.UP
            skipped_req_filter = Q(from_station__floor_no__lt=curr_floor_no)
        else:
            direction = Directions.DOWN
            skipped_req_filter = Q(from_station__floor_no__gt=curr_floor_no)
        skipped_req = pending_reqs.filter(skipped_req_filter, skip_count__gte=3).first()
        if not skipped_req:
            return True, direction
        skipped_req.skip_count = skipped_req.skip_count + 1
        skipped_req.save()
        return True, direction

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
    def get_nearest_request(pending_req, direction, curr_station):
        if direction == Directions.UP:
            filterQ = Q(from_station__floor_no__gt=curr_station.floor_no)
            nearest_req = pending_req.filter(filterQ).first()
        else:
            filterQ = Q(from_station__floor_no__lt=curr_station.floor_no)
            nearest_req = pending_req.filter(filterQ).last()
        return nearest_req

    @staticmethod
    def get_next_request(elevator_system):
        if not elevator_system.curr_station:
            return None, elevator_system.curr_direction
        pending_reqs = elevator_system.get_pending_requests()
        next_req, direction = ElevatorLogic._get_next_request_in_direction(
            pending_reqs, elevator_system
        )
        if next_req:
            return next_req, direction
        priority_req_found, direction = ElevatorLogic._get_high_priority_req(
            pending_reqs, elevator_system
        )
        if not priority_req_found:
            direction = ElevatorLogic._decide_direction(pending_reqs, elevator_system)
        next_req = ElevatorLogic.get_nearest_request(
            pending_reqs, direction, elevator_system.curr_station
        )
        return next_req, direction
