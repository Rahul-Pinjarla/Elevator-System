# Simple Elevator System

This is a simple elevator system logic implemented in Python, and backed by `Django`, this project provides a list of APIs to interact HTTPically to create & control elevator systems.

## Installation and Usage:
- Clone this repo, `cd` into the cloned folder, and create a venv using `python -m venv .venv`
- Run `pip install -r requirements.txt` to install the necessary packages.
- Start your `postgres` server and create a database with `elevator-system` as name.
- Create `.env` , copy & paste everything from `.env.dev` to `.env` and make sure to replace every `<Set your value here>` with your respective value.

## Things to remember:
### Elevator System
- Every Elevator System starts at floor 1 with defatlt direction set to `"UP"`. Floors are numbered `1,2....stations_count`
- Elevator system is Uni-directioral due to the one floor one button rule.
- You can create multiple Elevator Systems with any number of Elevator Stations.
- There will be only one elevator serving all floors in any given Elevator System.
  
### Elevator Station
- Every floor will have a Elevator Station which is the station that is responsible for opening and closing the doors.
- Every Elevator Station will have a single button. This button is used to call the Elevator to this floor.

### Elevator Request
- Every time there is a call from a floor's Elevator Station an Elevator Request will be recorded. 
- Every time someone selects a destination floor from within the elevator an elevator request will be saved or updated(if pending request exists).
- The nearest pending request in the Elevator System's `curr_direction` will be next request to serve, if None, the lift checks pending requests in the opposite direction, and if found, changes direction and moves to the nearest pending request station.

  - #### Pending Requests
    - Pending requests are the requests which are yet to be served with a working elevator.
    - Under maintenance elevator stations are excluded from pending requests.


## Features | API Reference
NOTE: In the API references given below replace the `<type:key>` with your respective value.
for example:
    this `/get_atom_bomb/<int:pk>` becomes `/get-atom-bomb/1` where `1` is our value for `pk`.

- Initiate Elevator System
  - Initiates a new elevator system
  - Gives back the new elevator instance to perform elevator operations mentioned below

    ```
        curl --location 'localhost:8000/elevator-app/initiate-elevator-system' \
        --header 'Content-Type: application/json' \
        --data '{
            "building_name": <str:building-name>,
            "stations_count": <int:count>
        }'
    ```

    returns the created elevator system details.

- Call Elevator
  - Mimics someone calling the elevator to the floor they are on
  - Adds a request with `curr_station` as `from_station` into the system.
    ```
    curl --location --request PATCH 'localhost:8000/elevator-app/call-elevator/<int:elevator_system_pk>/<int:floor_no>'
    ```
    returns the current elevator system state with success/fail message.

- Select floor
  - Mimics the process of a person selecting the destination floor after entering the lift.
    The `curr_station` of `ElevatorSystem` will be considered as the `from_station` for this req.
    By selecting a floor:
    - If a pending (not served) elevator call request from `curr_station` does not have a `to_station`
        (this means someone called the elevator at `curr_station`, entered the lift and selected `to_floor_no`)
        then the station at `to_floor_no` passed will be the `to_station` for this request.
    - If all pending requests already have their `to_station` details, then a new req
        from `curr_station` to station at `to_floor_no` will be created.
    - Thus, a new elevator request will be added to the elevator_system.
    ```
    curl --location --request PATCH 'localhost:8000/elevator-app/select-floor/<int:elevator_system_pk>/<int:floor_no>'
    ```
    returns the current elevator system state with success/fail message.

- Move Elevator
  - Mimics the flow of elevator door close, elevator moving to the next station, elevator door open.
  - Marks the pending requests to this station as served and updates the elevator system state.
    ```
    curl --location --request PATCH 'localhost:8000/elevator-app/move-elevator/<int:elevator_system_pk>'
    ```
    returns the current elevator system state with success/fail message.

- Mark Elevator Under Maintenance
  - Useful to mark or unmark an elevator station under maintenance.
   ```
    curl --location --request PATCH 'localhost:8000/elevator-app/mark-station-under-maintenance/<int:elevator-system-pk>/<int:floor_no>/<bool:flag>/'
   ```
    returns the current elevator system state with a success message.

- Get APIs
  - Along with the functional APIs above, this system also contains some GET APIs using which we can get the details of Elevator Sytems, Elevator Stations and Elevator-requests.
  - `curl --location 'localhost:8000/elevator-app/elevator-systems'`
    returns a list containing all the initiated elevator systems.
  - `curl --location 'localhost:8000/elevator-app/elevator-system/<int:elevator_system_pk>'` 
    returns all the necessary details of the Elevator System.
  - `curl --location 'localhost:8000/elevator-app/elevator-request/<int:elevator_request_pk'`
    returns the details of the elevator request.
  - `curl --location 'localhost:8000/elevator-app/elevator-station/<int:elevator_station_pk>'` 
    returns the details of the elevator station.