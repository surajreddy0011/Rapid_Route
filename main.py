import bson
import pymongo
import datetime
import os
import bcrypt
import flask
from bson import ObjectId
from bson.errors import InvalidId
from dns.e164 import query
from flask import Flask, render_template, request, redirect, session, flash
from datetime import datetime, timedelta

app = Flask(__name__)

my_client = pymongo.MongoClient("mongodb://localhost:27017")
my_database = my_client["Rapid_Route"]
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LICENSE_PATH = APP_ROOT + "/static/photos"

admin_collection = my_database["admin"]
bookings_collection = my_database["bookings"]
buses_collection = my_database["buses"]
drivers_collection = my_database["drivers"]
passengers_collection = my_database["customers"]
schedules_collection = my_database["schedules"]
payments_collection = my_database["payments"]
stations_collection = my_database["stations"]



admin_username = "admin"
admin_password = "admin"
app.secret_key = "rapid_route"


@app.route("/")
def index():
    return render_template("index 2.html")


@app.route("/admin")
def admin():
    return render_template("admin_login.html")


@app.route("/admin_login_action", methods=['post'])
def admin_login_action():
    username = request.form.get("username")
    password = request.form.get("password")
    print(username)
    print(password)
    if username == admin_username and password == admin_password:
        session["role"] = "admin"
        return redirect("/admin_home")
    else:
        return render_template("message.html", message="Invalid login details")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")

@app.route("/driver")
def driver():
    query = {}
    drivers = drivers_collection.find(query)
    return render_template("driver_regi.html", drivers=drivers)

@app.route("/driver_login")
def driver_login():
    return render_template("driver_login.html")

@app.route("/passenger")
def passenger():
    query = {}
    passengers = passengers_collection.find(query)
    return render_template("passenger_login.html",passengers=passengers)

@app.route("/passenger_login",methods=['POST'])
def passenger_login():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = passengers_collection.count_documents(query)
    if count > 0:
        passenger = passengers_collection.find_one(query)
        session['passenger_id'] = str(passenger['_id'])
        session['role'] = 'CUSTOMER'
        return redirect("/passenger_home")
    else:
        return render_template("message.html", message="Invalid login details")

@app.route("/passenger_home")
def passenger_home():
    return render_template("passenger_home.html")

@app.route("/passenger_registration")
def passenger_registration():
    return render_template("passenger_registration.html")

@app.route("/passenger_registration_action",methods=['POST'])
def passenger_registration_action():
    address = request.form.get('address')
    city = request.form.get('city')
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    encrypted_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    phone = request.form.get('phone')
    state = request.form.get('state')
    zip_code = request.form.get('zip_code')

    query = {"email": email}
    count = passengers_collection.count_documents(query)

    if count > 0:
        return render_template("message2.html", message="Duplicate Email")

    query = {"address": address,
             "city": city,
             "email": email,
             "name": name,
             "password": password,
             "phone":phone,
             "encrypted_password": encrypted_password,
             "state":state,
             "zip_code":zip_code}
    passengers_collection.insert_one(query)
    return render_template("message.html", message="Passenger added Successfully")


@app.route("/driver_login_action", methods=['POST'])
def driver_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = drivers_collection.count_documents(query)
    if count > 0:
        driver = drivers_collection.find_one(query)
        session['driver_id'] = str(driver['_id'])
        session['role'] = 'DRIVER'
        session['driver_name'] = driver['name']
        return redirect("/driver_home")
    else:
        return render_template("message.html", message="Invalid login details")

@app.route("/driver_registration_action",methods=['POST'])
def driver_registration_action():
    address = request.form.get('address')
    city = request.form.get('city')
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    encrypted_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    phone = request.form.get('phone')
    state = request.form.get('state')
    zip_code = request.form.get('zip_code')


    license = request.files.get("license")
    path = LICENSE_PATH + "/" + license.filename
    license.save(path)

    query = {"email": email}
    count = drivers_collection.count_documents(query)

    if count > 0:
        return render_template("message2.html", message="Duplicate Bus number")

    query = {"address": address,
             "city": city,
             "email": email,
             "name": name,
             "password": password,
             "encrypted_password": encrypted_password,
             "phone":phone,
             "state":state,
             "zip_code":zip_code,
             "license": license.filename,

             }
    drivers_collection.insert_one(query)
    return render_template("message.html", message="Driver added Successfully")


@app.route("/stations")
def stations():
    query = {}
    stations = stations_collection.find(query)
    stations = list(stations)
    message = request.args.get('message')
    return render_template("stations.html", message=message, stations = stations)


@app.route("/add_stations_action", methods=['POST'])
def add_stations_action():
    station_name = request.form.get('station_name')
    city = request.form.get('city')
    state = request.form.get('state')
    zip_code = request.form.get('zip_code')
    
    query = {"station_name": station_name}
    count = stations_collection.count_documents(query)
    if count > 0:
        return redirect("/stations?message=Station name already registered")
    
    query = {
        "station_name": station_name,
        "city": city,
        "state": state,
        "zip_code": zip_code
    }
    stations_collection.insert_one(query)
    return redirect("/stations?message=Station added successfully")

@app.route("/edit_station/<station_id>")
def edit_station(station_id):
    try:
        station = stations_collection.find_one({"_id": ObjectId(station_id)})
        if not station:
            return render_template("message.html", message="Station not found")
        return render_template("edit_station.html", station=station)
    except Exception as e:
        return render_template("message.html", message=f"An error occurred: {str(e)}")

@app.route("/update_station_action", methods=['POST'])
def update_station_action():
    try:
        station_id = request.form.get('station_id')
        station_name = request.form.get('station_name')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        
        # Check if another station with the same name exists (excluding this one)
        query = {
            "station_name": station_name,
            "_id": {"$ne": ObjectId(station_id)}
        }
        count = stations_collection.count_documents(query)
        if count > 0:
            return redirect(f"/edit_station/{station_id}?message=Station name already exists")
        
        # Update the station
        stations_collection.update_one(
            {"_id": ObjectId(station_id)},
            {"$set": {
                "station_name": station_name,
                "city": city,
                "state": state,
                "zip_code": zip_code
            }}
        )
        return redirect("/stations?message=Station updated successfully")
    except Exception as e:
        return render_template("message.html", message=f"An error occurred: {str(e)}")

@app.route("/delete_station/<station_id>")
def delete_station(station_id):
    try:
        # Check if the station is used in any schedules
        schedules = schedules_collection.find({
            "$or": [
                {"departure_station": ObjectId(station_id)},
                {"arrival_station": ObjectId(station_id)}
            ]
        })
        
        if schedules_collection.count_documents({
            "$or": [
                {"departure_station": ObjectId(station_id)},
                {"arrival_station": ObjectId(station_id)}
            ]
        }) > 0:
            return render_template("message.html", 
                                  message="Cannot delete this station as it is used in existing schedules.")
        
        # Delete the station
        result = stations_collection.delete_one({"_id": ObjectId(station_id)})
        if result.deleted_count > 0:
            return redirect("/stations?message=Station deleted successfully")
        else:
            return render_template("message.html", message="Station not found")
    except Exception as e:
        return render_template("message.html", message=f"An error occurred: {str(e)}")


@app.route("/buses")
def buses():
    query = {}
    drivers = drivers_collection.find(query)
    query = {}
    buses = buses_collection.find(query)
    return render_template("buses.html",drivers=drivers,buses=buses)

@app.route("/add_bus_action", methods=['POST'])
def add_bus_action():
    bus_name = request.form.get('bus_name')
    bus_number = request.form.get('bus_number')
    bus_type = request.form.get('bus_type')
    seats = request.form.get('seats')


    bus_Image = request.files.get('bus_Image')
    path = LICENSE_PATH + "/" + bus_Image.filename
    bus_Image.save(path)

    query = {"bus_number": bus_number}
    count = buses_collection.count_documents(query)

    if count > 0:
        return render_template("message2.html", message="Duplicate Bus number")

    query = {"bus_name": bus_name,
             "bus_number": bus_number,
             "bus_type": bus_type,
             "seats": seats,
             "bus_Image": bus_Image.filename,

             }

    buses_collection.insert_one(query)
    return render_template("message.html", message="Bus added Successfully")


@app.route("/schedules")
def schedules():
    driver_id = request.args.get("driver_id")
    bus_id = request.args.get("bus_id")
    
    print(f"Received parameters: bus_id={bus_id}, driver_id={driver_id}")
    
    # Validate that bus_id is a valid ObjectId if provided
    if bus_id:
        try:
            bus_id_obj = ObjectId(bus_id)
            # Get the bus details to display
            bus = buses_collection.find_one({"_id": bus_id_obj})
            if bus:
                print(f"Found bus: {bus.get('bus_name', 'Unknown')}")
        except Exception as e:
            print(f"Invalid bus ID: {e}")
            return render_template("message.html", message=f"Invalid bus ID format: {str(e)}")
    
    # Validate that driver_id is a valid ObjectId if provided
    if driver_id:
        try:
            driver_id_obj = ObjectId(driver_id)
            # Get the driver details to display
            driver = drivers_collection.find_one({"_id": driver_id_obj})
            if driver:
                print(f"Found driver: {driver.get('name', 'Unknown')}")
        except Exception as e:
            print(f"Invalid driver ID: {e}")
            return render_template("message.html", message=f"Invalid driver ID format: {str(e)}")
    
    stations = list(stations_collection.find({}))
    drivers = list(drivers_collection.find({}))
    buses = list(buses_collection.find({}))
    current_date = datetime.now().strftime("%m-%d-%Y")
    
    return render_template("schedules.html", 
                          driver_id=driver_id, 
                          bus_id=bus_id, 
                          stations=stations,
                          drivers=drivers,
                          buses=buses,
                          current_date=current_date)

@app.route("/add_schedules_action", methods=['POST'])
def add_schedules_action():
    try:
        # Get form data
        bus_id = request.form.get('bus_id')
        driver_id = request.form.get('driver_id')
        departure_station = request.form.get('departure_station')
        arrival_station = request.form.get('arrival_station')
        departure_platform = request.form.get('departure_platform')
        arrival_platform = request.form.get('arrival_platform')
        departure_time = request.form.get('departure_time')
        arrival_time = request.form.get('arrival_time')
        ticket_price = request.form.get('ticket_price')
        status = request.form.get('status', 'Scheduled')
        
        # Print received data for debugging
        print(f"Received form data: bus_id={bus_id}, driver_id={driver_id}")
        
        # Validate required fields
        if not driver_id or not departure_station or not arrival_station:
            return render_template("message.html", message="Missing required fields. Please fill all required fields.")

        # Check if the IDs are valid ObjectIds
        try:
            # Only convert bus_id to ObjectId if it's provided and not empty
            bus_id_obj = ObjectId(bus_id) if bus_id and bus_id.strip() else None
            driver_id_obj = ObjectId(driver_id)
            departure_station_obj = ObjectId(departure_station)
            arrival_station_obj = ObjectId(arrival_station)
        except Exception as e:
            print(f"Invalid ID format error: {e}")
            return render_template("message.html", message=f"Invalid ID format. Please select valid options. Error: {str(e)}")
        
        # Parse the datetime objects for comparison
        departure_datetime = datetime.strptime(departure_time, "%Y-%m-%dT%H:%M")
        arrival_datetime = datetime.strptime(arrival_time, "%Y-%m-%dT%H:%M")
        
        # Check for schedule conflicts if bus_id is provided
        if bus_id_obj:
            # Find all existing schedules for this bus
            existing_schedules = list(schedules_collection.find({"bus_id": bus_id_obj}))
            print(f"Found {len(existing_schedules)} existing schedules for bus {bus_id_obj}")
            
            # Check each schedule for overlap
            for schedule in existing_schedules:
                try:
                    existing_departure = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                    existing_arrival = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
                    
                    # Check for any overlap between schedules
                    if (departure_datetime <= existing_arrival and arrival_datetime >= existing_departure):
                        print(f"CONFLICT: New schedule {departure_datetime}-{arrival_datetime} overlaps with existing {existing_departure}-{existing_arrival}")
                        return render_template("message.html", 
                                            message="This bus already has a schedule during this time period. Please select a different time or bus.")
                except Exception as e:
                    print(f"Error comparing schedule times: {e}")
                    continue
        
        # Create the query dictionary
        query = {
            "departure_station": departure_station_obj,
            "arrival_station": arrival_station_obj,
            "driver_id": driver_id_obj,
            "departure_platform": departure_platform,
            "arrival_platform": arrival_platform,
            "arrival_time": arrival_time,
            "departure_time": departure_time,
            "ticket_price": ticket_price,
            "status": status
        }
        
        # Only add bus_id to the query if it's provided
        if bus_id_obj:
            query["bus_id"] = bus_id_obj
            print(f"Adding bus_id {bus_id_obj} to schedule")
        else:
            print("No bus_id provided for schedule")
        
        schedules_collection.insert_one(query)
        return render_template("message.html", message="Schedule added Successfully")
    except Exception as e:
        print(f"Unexpected error in add_schedules_action: {e}")
        return render_template("message.html", message=f"An unexpected error occurred: {str(e)}")


from datetime import datetime


@app.route("/view_schedules")
def view_schedules():
    schedules = list(schedules_collection.find({}))

    for schedule in schedules:
        try:
            # Format times
            dep = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
            arr = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
            schedule['departure_time_fmt'] = dep.strftime("%I:%M %p")
            schedule['arrival_time_fmt'] = arr.strftime("%I:%M %p")
            schedule['departure_day'] = dep.strftime("%m-%d-%Y")
            schedule['arrival_day'] = arr.strftime("%m-%d-%Y")
            duration = arr - dep
            total_minutes = int(duration.total_seconds() // 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            schedule['duration'] = f"{hours}h {minutes}m"
            
            # Make sure bus_id exists before trying to use it
            if 'bus_id' not in schedule or not schedule['bus_id']:
                schedule['bus_id'] = None
        except Exception as e:
            schedule['departure_time_fmt'] = "Invalid"
            schedule['arrival_time_fmt'] = "Invalid"
            schedule['duration'] = "Invalid"
            
    return render_template("view_schedules.html", 
                          schedules=schedules,
                          get_bus_name_by_bus_id=get_bus_name_by_bus_id,
                          get_station_name_by_station_id=get_station_name_by_station_id)

def get_bus_name_by_bus_id(bus_id):
    if not bus_id:
        return None
    try:
        # Make sure bus_id is a valid ObjectId
        if not isinstance(bus_id, ObjectId):
            bus_id = ObjectId(bus_id)
        query = {'_id': bus_id}
        bus = buses_collection.find_one(query)
        return bus
    except Exception as e:
        print(f"Error getting bus: {e}")
        return None

def get_station_name_by_station_id(station_id):
    if not station_id:
        return None
    try:
        # Make sure station_id is a valid ObjectId
        if not isinstance(station_id, ObjectId):
            station_id = ObjectId(station_id)
        query = {'_id': station_id}
        station = stations_collection.find_one(query)
        return station
    except Exception as e:
        print(f"Error getting station: {e}")
        return None



@app.route("/search_bus", methods=['GET', 'POST'])
def search_bus():
    stations = list(stations_collection.find({}))
    schedules = []
    selected_departure = request.values.get("departure_station")
    selected_arrival = request.values.get("arrival_station")
    travel_date = request.values.get("travel_date")
    
    if request.method == 'POST' or (selected_departure and selected_arrival):
        query = {}
        if selected_departure:
            query['departure_station'] = ObjectId(selected_departure)
        if selected_arrival:
            query['arrival_station'] = ObjectId(selected_arrival)
        if travel_date:
            query['departure_time'] = {'$regex': f'^{travel_date}'}

        schedules = list(schedules_collection.find(query))
        for schedule in schedules:
            try:
                dep = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                arr = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
                duration = arr - dep
                

                bus_details = None
                if 'bus_id' in schedule and schedule['bus_id']:
                    bus_details = get_bus_name_by_bus_id(schedule['bus_id'])
                
                # Get station names
                departure_station_name = "Unknown"
                arrival_station_name = "Unknown"
                if 'departure_station' in schedule:
                    dep_station = get_station_name_by_station_id(schedule['departure_station'])
                    if dep_station:
                        departure_station_name = dep_station.get('station_name', 'Unknown')
                
                if 'arrival_station' in schedule:
                    arr_station = get_station_name_by_station_id(schedule['arrival_station'])
                    if arr_station:
                        arrival_station_name = arr_station.get('station_name', 'Unknown')
                
                # Update schedule with formatted data
                schedule.update({
                    'departure_time_fmt': dep.strftime("%I:%M %p"),
                    'arrival_time_fmt': arr.strftime("%I:%M %p"),
                    'departure_day': dep.strftime("%m-%d-%Y"),
                    'arrival_day': arr.strftime("%m-%d-%Y"),
                    'duration': f"{duration.seconds//3600}h {(duration.seconds//60)%60}m",
                    'bus_details': bus_details or {'bus_name': 'Unknown', 'bus_type': 'Unknown', 'bus_Image': None},
                    'departure_station_name': departure_station_name,
                    'arrival_station_name': arrival_station_name
                })
            except Exception as e:
                print(f"Error processing schedule: {e}")
                schedule.update({
                    'departure_time_fmt': "Invalid",
                    'arrival_time_fmt': "Invalid",
                    'duration': "Invalid",
                    'bus_details': {'bus_name': 'Unknown', 'bus_type': 'Unknown', 'bus_Image': None},
                    'departure_station_name': "Unknown",
                    'arrival_station_name': "Unknown"
                })

    return render_template("search_bus.html", schedules=schedules, stations=stations,
                           selected_departure=selected_departure, selected_arrival=selected_arrival,
                           selected_date=travel_date)

@app.route("/book_ticket")
def book_ticket():
    bus_id = request.args.get("bus_id")
    schedule_id = request.args.get("schedule_id")
    bus = buses_collection.find_one({"_id": ObjectId(bus_id)})
    schedule = schedules_collection.find_one({"_id": ObjectId(schedule_id)}) if schedule_id else None

    # Get station names for display
    if schedule:
        dep_station = stations_collection.find_one({"_id": schedule["departure_station"]})
        arr_station = stations_collection.find_one({"_id": schedule["arrival_station"]})
        if dep_station:
            schedule['departure_station_name'] = dep_station['station_name']
        if arr_station:
            schedule['arrival_station_name'] = arr_station['station_name']
        
        # Format times
        try:
            dep = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
            arr = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
            schedule['departure_time_fmt'] = dep.strftime("%I:%M %p")
            schedule['arrival_time_fmt'] = arr.strftime("%I:%M %p")
            schedule['departure_day'] = dep.strftime("%m-%d-%Y")
            schedule['arrival_day'] = arr.strftime("%m-%d-%Y")
        except Exception as e:
            print(f"Error formatting times: {e}")

    total_seats = int(bus.get('seats', 40))
    seats_per_row = 4
    rows = (total_seats + seats_per_row - 1) // seats_per_row

    booked_seats = []
    if schedule_id:
        bookings = bookings_collection.find({"schedule_id": ObjectId(schedule_id)})
        for booking in bookings:
            booked_seats.extend(booking.get("seats", []))
    remaining_seats = total_seats % seats_per_row or seats_per_row

    return render_template("select_seats.html",
                           bus=bus,
                           schedule=schedule,
                           total_seats=total_seats,
                           rows=rows,
                           booked_seats=booked_seats,
                           bus_id=bus_id,
                           schedule_id=schedule_id,
                           remaining_seats=remaining_seats)

@app.route("/passenger_details")
def passenger_details():
    bus_id = request.args.get("bus_id")
    schedule_id = request.args.get("schedule_id")
    selected_seats = request.args.get("seats", "")
    
    if not selected_seats:
        return render_template("message.html", message="No seats selected. Please select seats first.")
    
    seats = selected_seats.split(',')
    
    bus = buses_collection.find_one({"_id": ObjectId(bus_id)})
    schedule = schedules_collection.find_one({"_id": ObjectId(schedule_id)})
    
    # Get station names for display
    if schedule:
        dep_station = stations_collection.find_one({"_id": schedule["departure_station"]})
        arr_station = stations_collection.find_one({"_id": schedule["arrival_station"]})
        if dep_station:
            schedule['departure_station_name'] = dep_station['station_name']
        if arr_station:
            schedule['arrival_station_name'] = arr_station['station_name']
        
        # Format times
        try:
            dep = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
            arr = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
            schedule['departure_time_fmt'] = dep.strftime("%I:%M %p")
            schedule['arrival_time_fmt'] = arr.strftime("%I:%M %p")
            schedule['departure_day'] = dep.strftime("%m-%d-%Y")
            schedule['arrival_day'] = arr.strftime("%m-%d-%Y")
        except Exception as e:
            print(f"Error formatting times: {e}")
    
    price_per_ticket = float(schedule.get("ticket_price", 0))
    total_price = price_per_ticket * len(seats)
    
    return render_template("passenger_details.html", 
                          bus=bus, 
                          schedule=schedule, 
                          seats=seats, 
                          bus_id=bus_id, 
                          schedule_id=schedule_id,
                          selected_seats=selected_seats,
                          total_price=total_price)

@app.route("/save_passenger_details", methods=['POST'])
def save_passenger_details():
    bus_id = request.form.get("bus_id")
    schedule_id = request.form.get("schedule_id")
    selected_seats = request.form.get("selected_seats")
    total_price = request.form.get("total_price")
    
    seats = selected_seats.split(',')
    
    # Create a list to store passenger details for each seat
    passengers = []
    
    for seat in seats:
        passenger_info = {
            "seat": seat,
            "name": request.form.get(f"name_{seat}"),
            "age": request.form.get(f"age_{seat}"),
            "gender": request.form.get(f"gender_{seat}")
        }
        passengers.append(passenger_info)
    
    # Store in session for use during payment
    session['passenger_details'] = passengers
    
    return redirect(f"/payment?bus_id={bus_id}&schedule_id={schedule_id}&seats={selected_seats}&total_price={total_price}")

@app.route("/payment")
def payment():
    bus_id = request.args.get("bus_id")
    schedule_id = request.args.get("schedule_id")
    selected_seats = request.args.get("seats", "")
    total_price = request.args.get("total_price", "0")
    
    # Check if we have passenger details
    if 'passenger_details' not in session:
        return redirect(f"/passenger_details?bus_id={bus_id}&schedule_id={schedule_id}&seats={selected_seats}")
    
    return render_template("payment.html", 
                          bus_id=bus_id, 
                          schedule_id=schedule_id,
                          seats=selected_seats, 
                          total_price=total_price)

@app.route("/payment_page_action", methods=['POST'])
def payment_page_action():
    if 'passenger_id' not in session:
        return redirect("/passenger")
        
    try:
        passenger_id = ObjectId(session['passenger_id'])
        bus_id = request.form.get("bus_id")
        schedule_id = request.form.get("schedule_id")
        seats = request.form.get("seats").split(',')
        total_price = request.form.get("total_price")
        
        # Get passenger details from session
        passenger_details = session.get('passenger_details', [])
        
        # Create the main booking
        booking = {
            "bus_id": ObjectId(bus_id),
            "schedule_id": ObjectId(schedule_id),
            "passenger_id": passenger_id,
            "seats": seats,
            "total_price": total_price,
            "booking_date": datetime.now(),
            "status": "Confirmed",
            "passenger_details": passenger_details  # Store passenger details in the booking
        }
        booking_id = bookings_collection.insert_one(booking).inserted_id
        
        # Create payment record
        payments_collection.insert_one({
            "booking_id": booking_id,
            "amount": total_price,
            "passenger_id": passenger_id,
            "payment_method": request.form.get("payment_method"),
            "card_holder_name": request.form.get("card_holder_name"),
            "card_number_last4": request.form.get("card_number", "")[-4:] if request.form.get("card_number") else "",
            "expiry_date": request.form.get("expiry_date"),
            "cvv": request.form.get("cvv"),
            "payment_date": datetime.now(),
            "status": "Completed"
        })
        
        # Create individual e-tickets for each seat
        e_tickets = []
        for passenger in passenger_details:
            e_ticket = {
                "ticket_id": str(ObjectId()),
                "seat_number": passenger["seat"],
                "passenger_name": passenger["name"],
                "passenger_age": passenger["age"],
                "passenger_gender": passenger["gender"],
                "passenger_id": passenger_id,
                "booking_id": booking_id,
                "schedule_id": ObjectId(schedule_id),
                "bus_id": ObjectId(bus_id),
                "issue_date": datetime.now()
            }
            e_tickets.append(e_ticket)
        
        # Clear passenger details from session
        if 'passenger_details' in session:
            session.pop('passenger_details')
        
        return render_template("booking_confirmation.html", 
                              booking_id=booking_id, 
                              e_tickets=e_tickets,
                              total_price=total_price)
    except Exception as e:
        print(f"Payment processing error: {str(e)}")
        return render_template("message.html", message=f"An error occurred during payment processing: {str(e)}")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/view_tickets")
def view_tickets():
    if 'passenger_id' not in session:
        return redirect("/passenger")
    
    passenger_id = ObjectId(session['passenger_id'])
    bookings = list(bookings_collection.find({"passenger_id": passenger_id}))
    
    for booking in bookings:
        schedule = schedules_collection.find_one({"_id": booking["schedule_id"]})
        if schedule:
            booking["schedule"] = schedule
            dep_station = stations_collection.find_one({"_id": schedule["departure_station"]})
            arr_station = stations_collection.find_one({"_id": schedule["arrival_station"]})
            if dep_station:
                booking["departure_station_name"] = dep_station["station_name"]
            if arr_station:
                booking["arrival_station_name"] = arr_station["station_name"]
            
            try:
                dep = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                arr = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
                booking['departure_time_fmt'] = dep.strftime("%I:%M %p")
                booking['arrival_time_fmt'] = arr.strftime("%I:%M %p")
                booking['departure_day'] = dep.strftime("%m-%d-%Y")
                booking['arrival_day'] = arr.strftime("%m-%d-%Y")
                
                # Calculate duration
                duration_minutes = int((arr - dep).total_seconds() / 60)
                hours = duration_minutes // 60
                minutes = duration_minutes % 60
                booking['duration'] = f"{hours}h {minutes}m"
            except Exception as e:
                print(f"Error formatting times: {e}")
        
        bus = buses_collection.find_one({"_id": booking["bus_id"]})
        if bus:
            booking["bus"] = bus
            
        # Ensure passenger_details is available in the template
        if "passenger_details" not in booking:
            # If passenger_details doesn't exist in older bookings, create a basic structure
            booking["passenger_details"] = []
            for seat in booking.get("seats", []):
                booking["passenger_details"].append({
                    "seat": seat,
                    "name": "Passenger",
                    "age": "N/A",
                    "gender": "N/A"
                })
    
    return render_template("view_tickets.html", bookings=bookings)

@app.route("/view_ticket/<booking_id>")
def view_ticket(booking_id):
    if 'passenger_id' not in session:
        return redirect("/passenger")
    try:
        booking = bookings_collection.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            return render_template("message.html", message="Ticket not found.")
        if str(booking.get("passenger_id", "")) != session['passenger_id']:
            return render_template("message.html", message="You don't have permission to view this ticket.")
        schedule = schedules_collection.find_one({"_id": booking["schedule_id"]})
        if schedule:
            dep_station = stations_collection.find_one({"_id": schedule["departure_station"]})
            arr_station = stations_collection.find_one({"_id": schedule["arrival_station"]})
            if dep_station:
                schedule["departure_station_name"] = dep_station["station_name"]
            if arr_station:
                schedule["arrival_station_name"] = arr_station["station_name"]
            try:
                dep = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                arr = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
                schedule['departure_time_fmt'] = dep.strftime("%I:%M %p")
                schedule['arrival_time_fmt'] = arr.strftime("%I:%M %p")
                schedule['departure_day'] = dep.strftime("%A, %b %d")
                schedule['arrival_day'] = arr.strftime("%A, %b %d")
                duration = arr - dep
                total_minutes = int(duration.total_seconds() // 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                schedule['duration'] = f"{hours}h {minutes}m"
            except Exception as e:
                schedule['departure_time_fmt'] = "Invalid"
                schedule['arrival_time_fmt'] = "Invalid"
                schedule['duration'] = "Invalid"
        bus = buses_collection.find_one({"_id": booking["bus_id"]})
        passenger = passengers_collection.find_one({"_id": booking["passenger_id"]})
        return render_template("ticket_details.html", 
                              booking=booking, 
                              schedule=schedule, 
                              bus=bus, 
                              passenger=passenger)
    except Exception as e:
        return render_template("message.html", message=f"An error occurred: {str(e)}")

@app.route("/cancel_ticket/<booking_id>", methods=['GET', 'POST'])
def cancel_ticket(booking_id):
    if 'passenger_id' not in session:
        return redirect("/passenger")
    
    try:
        booking = bookings_collection.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return render_template("message.html", message="Ticket not found.")

        if str(booking.get("passenger_id", "")) != session['passenger_id']:
            return render_template("message.html", message="You don't have permission to cancel this ticket.")

        if booking.get("status") == "Cancelled":
            return render_template("message.html", message="This ticket is already cancelled.")
        
        schedule = schedules_collection.find_one({"_id": booking["schedule_id"]})
        bus = buses_collection.find_one({"_id": booking["bus_id"]})
        passenger = passengers_collection.find_one({"_id": booking["passenger_id"]})
        

        refund_percentage = 0
        refund_amount = 0
        refund_message = "No refund is available for this cancellation."
        hours_before_departure = 0
        
        try:
            if schedule and 'departure_time' in schedule:

                departure_time = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                current_time = datetime.now()
                time_difference = departure_time - current_time
                hours_before_departure = time_difference.total_seconds() / 3600
                
                if hours_before_departure < 3:
                    refund_percentage = 0
                    refund_message = "No refund is available for cancellations less than 3 hours before departure."
                elif hours_before_departure < 6:
                    refund_percentage = 20
                    refund_message = "You will receive a 20% refund for cancellations between 3-6 hours before departure."
                elif hours_before_departure < 24:
                    refund_percentage = 50
                    refund_message = "You will receive a 50% refund for cancellations between 6-24 hours before departure."
                elif hours_before_departure < 48:
                    refund_percentage = 70
                    refund_message = "You will receive a 70% refund for cancellations between 24-48 hours before departure."
                else:
                    refund_percentage = 100
                    refund_message = "You will receive a full refund for cancellations more than 48 hours before departure."
                
                total_price = float(booking.get("total_price", 0))
                refund_amount = (total_price * refund_percentage) / 100
                
                dep_station = stations_collection.find_one({"_id": schedule["departure_station"]})
                arr_station = stations_collection.find_one({"_id": schedule["arrival_station"]})
                if dep_station:
                    schedule["departure_station_name"] = dep_station["station_name"]
                if arr_station:
                    schedule["arrival_station_name"] = arr_station["station_name"]
                
                dep = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                arr = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
                schedule['departure_time_fmt'] = dep.strftime("%I:%M %p")
                schedule['arrival_time_fmt'] = arr.strftime("%I:%M %p")
                schedule['departure_day'] = dep.strftime("%m-%d-%Y")  # Changed to MM-DD-YYYY
                schedule['arrival_day'] = arr.strftime("%m-%d-%Y")    # Changed to MM-DD-YYYY
                
            else:
                refund_message = "Refund information could not be calculated due to missing schedule data."
                
        except Exception as e:
            print(f"Error calculating refund: {e}")
            refund_message = "Refund information could not be calculated due to an error."
        
        if request.method == 'POST':
            bookings_collection.update_one(
                {"_id": ObjectId(booking_id)},
                {"$set": {
                    "status": "Cancelled", 
                    "cancelled_at": datetime.now(),
                    "refund_percentage": refund_percentage,
                    "refund_amount": refund_amount
                }}
            )
            
            if refund_percentage > 0:
                refund_data = {
                    "booking_id": ObjectId(booking_id),
                    "passenger_id": booking["passenger_id"],
                    "amount": refund_amount,
                    "percentage": refund_percentage,
                    "status": "Processing",
                    "created_at": datetime.now()
                }

            
            return render_template("message.html", 
                                  message=f"Your ticket has been successfully cancelled. {refund_message}")
        
        return render_template("cancel_confirmation.html", 
                              booking=booking, 
                              schedule=schedule, 
                              bus=bus, 
                              passenger=passenger,
                              refund_percentage=refund_percentage,
                              refund_amount=refund_amount,
                              refund_message=refund_message)
        
    except Exception as e:
        return render_template("message.html", message=f"An error occurred: {str(e)}")

@app.route("/cancel_seat/<booking_id>/<seat>", methods=['GET', 'POST'])
def cancel_seat(booking_id, seat):
    if 'passenger_id' not in session:
        return redirect("/passenger")
    
    try:
        booking = bookings_collection.find_one({"_id": ObjectId(booking_id)})
        
        if not booking:
            return render_template("message.html", message="Ticket not found.")

        if str(booking.get("passenger_id", "")) != session['passenger_id']:
            return render_template("message.html", message="You don't have permission to cancel this ticket.")

        if booking.get("status") == "Cancelled":
            return render_template("message.html", message="This ticket is already cancelled.")
        
        if seat not in booking.get("seats", []):
            return render_template("message.html", message="Selected seat not found in this booking.")
        
        schedule = schedules_collection.find_one({"_id": booking["schedule_id"]})
        bus = buses_collection.find_one({"_id": booking["bus_id"]})
        passenger = passengers_collection.find_one({"_id": booking["passenger_id"]})
        
        # Calculate refund for a single seat
        refund_percentage = 0
        seat_price = float(booking.get("total_price", 0)) / len(booking.get("seats", []))
        refund_amount = 0
        refund_message = "No refund is available for this cancellation."
        hours_before_departure = 0
        
        try:
            if schedule and 'departure_time' in schedule:
                departure_time = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                current_time = datetime.now()
                time_difference = departure_time - current_time
                hours_before_departure = time_difference.total_seconds() / 3600
                
                # Set refund percentage based on how early they're cancelling
                if hours_before_departure > 72:  # More than 3 days
                    refund_percentage = 100
                    refund_message = "Full refund will be processed to your original payment method within 5-7 business days."
                elif hours_before_departure > 48:  # 2-3 days
                    refund_percentage = 75
                    refund_message = "75% refund will be processed to your original payment method within 5-7 business days."
                elif hours_before_departure > 24:  # 1-2 days
                    refund_percentage = 50
                    refund_message = "50% refund will be processed to your original payment method within 5-7 business days."
                elif hours_before_departure > 12:  # 12-24 hours
                    refund_percentage = 25
                    refund_message = "25% refund will be processed to your original payment method within 5-7 business days."
                else:
                    refund_percentage = 0
                    refund_message = "No refund is available for cancellations less than 12 hours before departure."
                
                refund_amount = (seat_price * refund_percentage) / 100
            
        except Exception as e:
            print(f"Error calculating refund: {e}")
        
        if request.method == 'POST':
            # Remove the seat from the booking
            remaining_seats = [s for s in booking["seats"] if s != seat]
            
            # Also remove the passenger details for this seat
            remaining_passenger_details = []
            if "passenger_details" in booking:
                remaining_passenger_details = [p for p in booking["passenger_details"] if p["seat"] != seat]
            
            if not remaining_seats:
                # If no seats remain, cancel the entire booking
                bookings_collection.update_one(
                    {"_id": ObjectId(booking_id)},
                    {"$set": {
                        "status": "Cancelled", 
                        "cancelled_at": datetime.now(),
                        "refund_percentage": refund_percentage,
                        "refund_amount": refund_amount
                    }}
                )
            else:
                # Update the booking with remaining seats and recalculate total price
                new_total_price = float(booking.get("total_price", 0)) - seat_price
                
                # Add cancellation info for the specific seat
                if "cancelled_seats" not in booking:
                    booking["cancelled_seats"] = []
                
                cancelled_seat_info = {
                    "seat": seat,
                    "cancelled_at": datetime.now(),
                    "refund_percentage": refund_percentage,
                    "refund_amount": refund_amount
                }
                
                # Find passenger details for the cancelled seat
                cancelled_passenger = None
                if "passenger_details" in booking:
                    for p in booking["passenger_details"]:
                        if p["seat"] == seat:
                            cancelled_passenger = p
                            break
                
                if cancelled_passenger:
                    cancelled_seat_info["passenger"] = cancelled_passenger
                
                bookings_collection.update_one(
                    {"_id": ObjectId(booking_id)},
                    {"$set": {
                        "seats": remaining_seats,
                        "passenger_details": remaining_passenger_details,
                        "total_price": str(new_total_price),
                        "partial_cancellation": True
                    },
                    "$push": {
                        "cancelled_seats": cancelled_seat_info
                    }}
                )
            
            if refund_percentage > 0:
                refund_data = {
                    "booking_id": ObjectId(booking_id),
                    "passenger_id": booking["passenger_id"],
                    "seat": seat,
                    "amount": refund_amount,
                    "percentage": refund_percentage,
                    "status": "Processing",
                    "created_at": datetime.now()
                }
                # Add code to store refund data if you have a refunds collection
            
            return render_template("message.html", 
                                  message=f"Your seat {seat} has been successfully cancelled. {refund_message}")
        
        return render_template("cancel_seat_confirmation.html", 
                              booking=booking,
                              seat=seat,
                              schedule=schedule, 
                              bus=bus, 
                              passenger=passenger,
                              refund_percentage=refund_percentage,
                              refund_amount=refund_amount,
                              refund_message=refund_message)
        
    except Exception as e:
        return render_template("message.html", message=f"An error occurred: {str(e)}")

@app.route("/driver_home")
def driver_home():
    if 'driver_id' not in session or session['role'] != 'DRIVER':
        return redirect("/driver_login")
    
    driver_id = ObjectId(session['driver_id'])
    driver = drivers_collection.find_one({"_id": driver_id})
    
    # Find buses assigned to this driver
    assigned_buses = list(buses_collection.find({"driver_id": driver_id}))
    
    # If no buses are directly assigned with driver_id field, check for driver assignment in schedules
    if not assigned_buses:
        # Find all schedules where this driver is assigned
        driver_schedules = list(schedules_collection.find({"driver_id": driver_id}))
        
        # Get unique bus IDs from these schedules
        bus_ids = set()
        for schedule in driver_schedules:
            if 'bus_id' in schedule:
                bus_ids.add(schedule['bus_id'])
        
        # Fetch the bus details
        if bus_ids:
            assigned_buses = list(buses_collection.find({"_id": {"$in": list(bus_ids)}}))
    
    print(f"Found {len(assigned_buses)} buses assigned to driver")
    
    bus_ids = [bus["_id"] for bus in assigned_buses]
    upcoming_schedules = []
    recent_bookings = []
    total_trips = 0
    completed_trips = 0
    upcoming_trips = 0
    total_passengers = 0
    
    if bus_ids:
        upcoming_schedules = list(schedules_collection.find({
            "bus_id": {"$in": bus_ids},
            "departure_time": {"$gte": datetime.now().strftime("%Y-%m-%dT%H:%M")}
        }).sort("departure_time", 1).limit(5))
        
        # Format the dates for display
        for schedule in upcoming_schedules:
            try:
                if 'departure_time' in schedule:
                    dep_time = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                    schedule['departure_time_fmt'] = dep_time.strftime("%I:%M %p")
                    schedule['departure_date'] = dep_time.strftime("%b %d, %Y")
                
                if 'arrival_time' in schedule:
                    arr_time = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
                    schedule['arrival_time_fmt'] = arr_time.strftime("%I:%M %p")
                
                # Get station names
                if 'departure_station' in schedule:
                    dep_station = stations_collection.find_one({"_id": schedule["departure_station"]})
                    if dep_station:
                        schedule['departure_station_name'] = dep_station['station_name']
                
                if 'arrival_station' in schedule:
                    arr_station = stations_collection.find_one({"_id": schedule["arrival_station"]})
                    if arr_station:
                        schedule['arrival_station_name'] = arr_station['station_name']
            except Exception as e:
                print(f"Error formatting schedule: {e}")
        

        all_schedules = list(schedules_collection.find({"bus_id": {"$in": bus_ids}}))
        all_schedule_ids = [schedule["_id"] for schedule in all_schedules]
        

        total_trips = len(all_schedules)
        completed_trips = schedules_collection.count_documents({
            "bus_id": {"$in": bus_ids},
            "status": "Completed"
        })
        upcoming_trips = schedules_collection.count_documents({
            "bus_id": {"$in": bus_ids},
            "departure_time": {"$gte": datetime.now().strftime("%Y-%m-%dT%H:%M")},
            "status": {"$ne": "Cancelled"}
        })
        

        if all_schedule_ids:
            recent_bookings = list(bookings_collection.find(
                {"schedule_id": {"$in": all_schedule_ids}}
            ).sort("_id", -1).limit(5))
            

            all_bookings = list(bookings_collection.find({"schedule_id": {"$in": all_schedule_ids}}))
            for booking in all_bookings:
                if "seats" in booking:
                    total_passengers += len(booking["seats"])
    
    return render_template(
        "driver_home.html",
        driver=driver,
        assigned_buses=assigned_buses,
        upcoming_schedules=upcoming_schedules,
        recent_bookings=recent_bookings,
        total_trips=total_trips,
        completed_trips=completed_trips,
        upcoming_trips=upcoming_trips,
        total_passengers=total_passengers
    )

@app.route("/driver_schedules")
def driver_schedules():
    if 'driver_id' not in session or session['role'] != 'DRIVER':
        return redirect("/driver_login")
    
    driver_id = ObjectId(session['driver_id'])
    

    assigned_buses = list(buses_collection.find({"driver_id": driver_id}))
    

    if not assigned_buses:
        driver_schedules = list(schedules_collection.find({"driver_id": driver_id}))
        bus_ids = set()
        for schedule in driver_schedules:
            if 'bus_id' in schedule:
                bus_ids.add(schedule['bus_id'])
        
        if bus_ids:
            assigned_buses = list(buses_collection.find({"_id": {"$in": list(bus_ids)}}))
    
    bus_ids = [bus["_id"] for bus in assigned_buses]
    

    print(f"Driver ID: {driver_id}")
    print(f"Found {len(assigned_buses)} buses assigned to driver")
    print(f"Bus IDs: {bus_ids}")
    

    schedules = []
    if bus_ids:
        schedules = list(schedules_collection.find({"bus_id": {"$in": bus_ids}}))
    

    if not schedules:
        schedules = list(schedules_collection.find({"driver_id": driver_id}))
    
    print(f"Found {len(schedules)} schedules for driver")
    
    for schedule in schedules:
        try:
            if 'bus_id' in schedule:
                bus = buses_collection.find_one({"_id": schedule["bus_id"]})
                if bus:
                    schedule['bus_name'] = bus.get('bus_name', 'Unknown')
                    schedule['bus_number'] = bus.get('bus_number', 'Unknown')
                    schedule['bus_type'] = bus.get('bus_type', 'Unknown')
            
            # Format times
            if 'departure_time' in schedule:
                dep = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                schedule['departure_time_fmt'] = dep.strftime("%I:%M %p")
                schedule['departure_day'] = dep.strftime("%m-%d-%Y")
            
            if 'arrival_time' in schedule:
                arr = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
                schedule['arrival_time_fmt'] = arr.strftime("%I:%M %p")
                schedule['arrival_day'] = arr.strftime("%m-%d-%Y")
            
            # Calculate duration
            if 'departure_time' in schedule and 'arrival_time' in schedule:
                dep_time = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                arr_time = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
                duration = arr_time - dep_time
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                schedule['duration'] = f"{hours}h {minutes}m"
            
            # Get station names
            if 'departure_station' in schedule:
                dep_station = stations_collection.find_one({"_id": schedule["departure_station"]})
                if dep_station:
                    schedule['departure_station_name'] = dep_station['station_name']
            
            if 'arrival_station' in schedule:
                arr_station = stations_collection.find_one({"_id": schedule["arrival_station"]})
                if arr_station:
                    schedule['arrival_station_name'] = arr_station['station_name']
            
        except Exception as e:
            print(f"Error formatting schedule: {e}")
            schedule['departure_time_fmt'] = "Invalid"
            schedule['arrival_time_fmt'] = "Invalid"
            schedule['duration'] = "Invalid"
    
    return render_template("driver_schedules.html", 
                          schedules=schedules, 
                          stations_collection=stations_collection,
                          buses_collection=buses_collection)

@app.route("/driver_bookings")
def driver_bookings():
    if 'driver_id' not in session or session['role'] != 'DRIVER':
        return redirect("/driver_login")
    
    driver_id = ObjectId(session['driver_id'])
    
    print(f"Driver ID: {driver_id}")
    
    # Find buses assigned to this driver
    assigned_buses = list(buses_collection.find({"driver_id": driver_id}))
    
    # If no buses are directly assigned, check schedules
    if not assigned_buses:
        driver_schedules = list(schedules_collection.find({"driver_id": driver_id}))
        bus_ids = set()
        for schedule in driver_schedules:
            if 'bus_id' in schedule:
                bus_ids.add(schedule['bus_id'])
        
        if bus_ids:
            assigned_buses = list(buses_collection.find({"_id": {"$in": list(bus_ids)}}))
    
    bus_ids = [bus["_id"] for bus in assigned_buses]
    
    print(f"Found {len(assigned_buses)} buses assigned to driver")
    print(f"Bus IDs: {bus_ids}")
    
    # Get schedules either by bus_id or directly by driver_id
    schedules = []
    if bus_ids:
        schedules = list(schedules_collection.find({"bus_id": {"$in": bus_ids}}))
    
    # If no schedules found by bus_id, try finding by driver_id directly
    if not schedules:
        schedules = list(schedules_collection.find({"driver_id": driver_id}))
    
    schedule_ids = [schedule["_id"] for schedule in schedules]
    
    print(f"Found {len(schedules)} schedules for driver's buses")
    print(f"Schedule IDs: {schedule_ids}")
    
    bookings = []
    if schedule_ids:
        bookings = list(bookings_collection.find({"schedule_id": {"$in": schedule_ids}}))
        print(f"Found {len(bookings)} bookings for driver's schedules")
        
        # Process each booking to add additional information
        for booking in bookings:
            try:
                # Add passenger information
                if 'passenger_id' in booking:
                    passenger = passengers_collection.find_one({"_id": booking["passenger_id"]})
                    if passenger:
                        booking['passenger_name'] = passenger.get('name', 'Unknown')
                        booking['passenger_phone'] = passenger.get('phone', 'N/A')
                        booking['passenger_email'] = passenger.get('email', 'N/A')
                
                # Add schedule and route information
                if 'schedule_id' in booking:
                    schedule = schedules_collection.find_one({"_id": booking["schedule_id"]})
                    if schedule:
                        # Get departure and arrival station names
                        if 'departure_station' in schedule:
                            dep_station = stations_collection.find_one({"_id": schedule["departure_station"]})
                            if dep_station:
                                booking['departure_station'] = dep_station.get('station_name', 'Unknown')
                        
                        if 'arrival_station' in schedule:
                            arr_station = stations_collection.find_one({"_id": schedule["arrival_station"]})
                            if arr_station:
                                booking['arrival_station'] = arr_station.get('station_name', 'Unknown')
                        
                        # Create route string
                        if 'departure_station' in booking and 'arrival_station' in booking:
                            booking['route'] = f"{booking['departure_station']} to {booking['arrival_station']}"
                        
                        # Format travel date
                        if 'departure_time' in schedule:
                            try:
                                dep_time = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                                booking['travel_date'] = dep_time.strftime("%A, %B %d, %Y")
                                booking['travel_time'] = dep_time.strftime("%I:%M %p")
                            except Exception as e:
                                print(f"Error formatting date: {e}")
                                booking['travel_date'] = schedule['departure_time']
            except Exception as e:
                print(f"Error processing booking {booking.get('_id')}: {e}")
    
    return render_template("driver_bookings.html", bookings=bookings)

@app.route("/driver_availability")
def driver_availability():
    if 'driver_id' not in session or session['role'] != 'DRIVER':
        return redirect("/driver_login")
    
    driver_id = ObjectId(session['driver_id'])
    driver = drivers_collection.find_one({"_id": driver_id})
    

    availability = []
    if driver and 'availability' in driver:
        availability = driver['availability']
    

    for record in availability:
        if 'date' in record:
            record['formatted_date'] = record['date'].strftime("%m-%d-%Y") if isinstance(record['date'], datetime) else record['date']
    

    today = datetime.now()
    current_month = today.month
    current_year = today.year
    

    calendar_data = []
    

    first_day = datetime(current_year, current_month, 1)
    if current_month == 12:
        last_day = datetime(current_year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
    
    num_days = last_day.day
    

    first_weekday = first_day.weekday()
    

    for i in range(first_weekday):
        calendar_data.append({
            "day": "",
            "date": "",
            "class": "other-month",
            "available": False
        })
    

    for day in range(1, num_days + 1):
        current_date = datetime(current_year, current_month, day)
        is_today = (current_date.date() == today.date())
        

        is_available = False
        for record in availability:
            if 'date' in record and isinstance(record['date'], datetime):
                if record['date'].date() == current_date.date() and record['status'] == 'available':
                    is_available = True
                    break
        
        calendar_data.append({
            "day": day,
            "date": current_date.strftime("%Y-%m-%d"),
            "class": "today" if is_today else "",
            "available": is_available
        })
    
    return render_template(
        "driver_availability.html",
        driver=driver,
        availability=availability,
        calendar_data=calendar_data,
        current_month=today.strftime("%B %Y")
    )

@app.route("/update_driver_availability", methods=['POST'])
def update_driver_availability():
    if 'driver_id' not in session or session['role'] != 'DRIVER':
        return redirect("/driver_login")
    
    driver_id = ObjectId(session['driver_id'])
    date = request.form.get('date')
    status = request.form.get('status')
    

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return render_template("message.html", message="Invalid date format")
    

    driver = drivers_collection.find_one({"_id": driver_id})
    

    if 'availability' not in driver:
        drivers_collection.update_one(
            {"_id": driver_id},
            {"$set": {"availability": []}}
        )
        driver['availability'] = []
    

    existing_index = None
    for i, record in enumerate(driver['availability']):
        if 'date' in record and isinstance(record['date'], datetime):
            if record['date'].date() == date_obj.date():
                existing_index = i
                break
    
    if existing_index is not None:

        driver['availability'][existing_index]['status'] = status
        drivers_collection.update_one(
            {"_id": driver_id},
            {"$set": {"availability": driver['availability']}}
        )
    else:

        new_record = {
            "date": date_obj,
            "status": status,
            "created_at": datetime.now()
        }
        drivers_collection.update_one(
            {"_id": driver_id},
            {"$push": {"availability": new_record}}
        )
    
    return redirect("/driver_availability")

@app.route("/view_passenger_ticket/<booking_id>")
def view_passenger_ticket(booking_id):
    if 'driver_id' not in session or session['role'] != 'DRIVER':
        return redirect("/driver_login")
    
    # Return a message indicating this feature is disabled
    return render_template("message.html", message="This feature has been disabled for driver accounts.")

@app.route("/schedule_bookings/<schedule_id>")
def schedule_bookings(schedule_id):
    if 'driver_id' not in session or session['role'] != 'DRIVER':
        return redirect("/driver_login")
    
    try:
        # Get the schedule details
        schedule = schedules_collection.find_one({"_id": ObjectId(schedule_id)})
        if not schedule:
            return render_template("message.html", message="Schedule not found.")
        
        # Get bus details
        bus = None
        if 'bus_id' in schedule:
            bus = buses_collection.find_one({"_id": schedule["bus_id"]})
            if bus:
                schedule['bus_name'] = bus.get('bus_name', 'Unknown')
                schedule['bus_number'] = bus.get('bus_number', 'Unknown')
                schedule['bus_type'] = bus.get('bus_type', 'Unknown')
        
        # Get station details
        if 'departure_station' in schedule:
            dep_station = stations_collection.find_one({"_id": schedule["departure_station"]})
            if dep_station:
                schedule['departure_station_name'] = dep_station.get('station_name', 'Unknown')
        
        if 'arrival_station' in schedule:
            arr_station = stations_collection.find_one({"_id": schedule["arrival_station"]})
            if arr_station:
                schedule['arrival_station_name'] = arr_station.get('station_name', 'Unknown')
        
        # Format times
        if 'departure_time' in schedule:
            try:
                dep_time = datetime.strptime(schedule['departure_time'], "%Y-%m-%dT%H:%M")
                schedule['departure_time_fmt'] = dep_time.strftime("%I:%M %p")
                schedule['departure_date'] = dep_time.strftime("%b %d, %Y")
            except:
                schedule['departure_time_fmt'] = "Invalid"
                schedule['departure_date'] = "Invalid"
        
        if 'arrival_time' in schedule:
            try:
                arr_time = datetime.strptime(schedule['arrival_time'], "%Y-%m-%dT%H:%M")
                schedule['arrival_time_fmt'] = arr_time.strftime("%I:%M %p")
                schedule['arrival_date'] = arr_time.strftime("%b %d, %Y")
            except:
                schedule['arrival_time_fmt'] = "Invalid"
                schedule['arrival_date'] = "Invalid"
        
        # Get bookings for this schedule
        bookings = list(bookings_collection.find({"schedule_id": ObjectId(schedule_id)}))
        
        # Add passenger details to each booking
        for booking in bookings:
            passenger = passengers_collection.find_one({"_id": booking["passenger_id"]})
            if passenger:
                booking['passenger_name'] = passenger.get('name', 'Unknown')
                booking['passenger_phone'] = passenger.get('phone', 'N/A')
                booking['passenger_email'] = passenger.get('email', 'N/A')
        
        return render_template("schedule_bookings.html", 
                              schedule=schedule, 
                              bookings=bookings)
    except Exception as e:
        return render_template("message.html", message=f"An error occurred: {str(e)}")

@app.route("/update_schedule_status/<schedule_id>")
def update_schedule_status(schedule_id):
    if 'driver_id' not in session or session['role'] != 'DRIVER':
        return redirect("/driver_login")
    

    new_status = request.args.get('status', 'scheduled')
    

    valid_statuses = ['scheduled', 'in-progress', 'completed', 'cancelled']
    if new_status.lower() not in valid_statuses:
        new_status = 'scheduled'
    

    display_status = new_status.capitalize()
    if new_status == 'in-progress':
        display_status = 'In-Progress'
    
    try:

        schedules_collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": {"status": display_status}}
        )
        

        schedules_collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": {f"status_changed_at": datetime.now()}}
        )
        

        return redirect("/driver_schedules")
    except Exception as e:
        return render_template("message.html", message=f"Error updating status: {str(e)}")


@app.route("/driver_change_password")
def driver_change_password():
    return render_template("driver_change_password.html")


@app.route("/driver_change_password_action", methods=['POST'])
def driver_change_password_action():
    driver_id = session['driver_id']
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if new_password != confirm_password:
        flash("New password and confirm password do not match","error")
        return redirect("/driver_change_password")
    driver = drivers_collection.find_one({"_id": ObjectId(driver_id)})
    if driver and driver["password"] == current_password:
        drivers_collection.update_one({"_id": ObjectId(driver_id)}, {"$set":{"password": new_password}})
        flash("Password changed successfully","success")
    else:
        flash("Current password is incorrect","error")
    return redirect("/driver_change_password")

app.run(debug=True)
