# import pandas as pd
#
# from shortest_path import generate_graph
#
# save_path = "data/"
#
# user_id = "60f4d5c5b5f0f0e5e8b2b5c9"
# latitude = "6.828828828828828"
# longitude = "79.86386702251839"
# radius = "303.5087719298246"
# start_time_restrictions = "7.00AM"
# end_time_restrictions = "7.00PM"
# accessibility = "Wheelchair-accessible car park, Wheelchair-accessible entrance"
# historical_contexts = "Ancient Buddhist monastery"
# hands_on_activities = "Photography, Sightseeing, Relaxing"
# location_id = "652b9d229c8deef2485bf8e2"
#
# # users.to_csv(save_path + "users.csv", index=False)
# # interactions.to_csv(save_path + "interactions.csv", index=False)
# locations = pd.read_csv(save_path + "locations.csv")
#
# print(locations[locations["_id"] == location_id])
#
# # current_location = (6.9271, 79.8612)
# current_location = (float(latitude), float(longitude))
#
# G, hamiltonian_cycle = generate_graph(current_location, locations.head())
# print(hamiltonian_cycle)
#
# # add 0 as
#
# # from locations find the location_ids in the hamiltonian_cycle and get all the details of those locations
# locations_in_hamiltonian_cycle = locations[locations["_id"].isin(hamiltonian_cycle)]
# print(locations_in_hamiltonian_cycle)
#
#
#





import math
import random
from datetime import time

import pandas as pd
from dateutil.parser import parser

from shortest_path import generate_graph, plot_hamiltonian_cycle


def haversine_distance(lat1, lon1, lat2, lon2):
    r = 6371000  # Radius of the Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # kilometers
    return (r * c) / 1000


def is_within_radius(row, current_latitude, current_longitude, radius):
    distance = haversine_distance(current_latitude, current_longitude, row['latitude'], row['longitude'])
    return distance <= radius


# Function to convert time string to datetime.time object
def convert_time_string_to_time(time_string):
    # parse time string to time
    return parser().parse(time_string).time()


# Function to check if a time range overlaps with the operating hours of a row
def is_within_time_range(row, start_time, end_time):
    open_time = convert_time_string_to_time(row['openTime'])
    close_time = convert_time_string_to_time(row['closeTime'])

    # If the place is open 24 hours
    if open_time == time(0, 0) and close_time == time(0, 0):
        return True

    # Check for overlap
    return (start_time <= open_time <= end_time) or (start_time <= close_time <= end_time)


def check_accessibility(row, accessibility_values, column_to_be_checked='accessibility'):
    row_accessibility_values = set(row[column_to_be_checked].split(","))

    return any(value in row_accessibility_values for value in accessibility_values)


def filter_data(shortest_path, locations):
    ################################################ Radius ################################################
    # filter locations by radius
    locations = locations[locations.apply(
        lambda row: is_within_radius(row, shortest_path['latitude'], shortest_path['longitude'],
                                     shortest_path['distanceRadiusValue']), axis=1)]

    print("Location_by_radius")
    print(locations)
    print("\n\n\n\n")

    ################################################ Time ################################################
    # Convert "7.00AM - 7.00PM" to datetime.time objects
    start_time = convert_time_string_to_time(shortest_path['updatedData']["Time Restrictions"].split("-")[0])
    end_time = convert_time_string_to_time(shortest_path['updatedData']["Time Restrictions"].split("-")[1])

    print(start_time)
    print(end_time)

    # Filter locations by time
    locations = locations[locations.apply(lambda row: is_within_time_range(row, start_time, end_time), axis=1)]

    print(locations)
    print("\n\n\n\n")

    ################################################ Accessibility ################################################
    # if filter is "Not selected" then don't filter
    if shortest_path['updatedData']["Accessibility"] != "Not selected":
        # Split the given accessibility variable by comma and strip whitespace
        accessibility_values = [value.strip() for value in shortest_path['updatedData']["Accessibility"].split(",")]

        locations = locations[locations.apply(lambda row: check_accessibility(row, accessibility_values), axis=1)]

        print(locations)

    ################################################ Historical Contexts ################################################
    # if filter is "Not selected" then don't filter
    if shortest_path['updatedData']["Historical Contexts"] != "Not selected":
        # Split the given historical context variable by comma and strip whitespace
        historical_context_values = [value.strip() for value in
                                     shortest_path['updatedData']["Historical Contexts"].split(",")]

        locations = locations[locations.apply(
            lambda row: check_accessibility(row, historical_context_values, column_to_be_checked='historical_context'),
            axis=1)]

        print(locations)

    ################################################ Hands-On Activities ################################################
    # if filter is "Not selected" then don't filter
    if shortest_path['updatedData']["Hands-On Activities"] != "Not selected":
        # Split the given hands on activities variable by comma and strip whitespace
        hands_on_activities_values = [value.strip() for value in
                                      shortest_path['updatedData']["Hands-On Activities"].split(",")]

        locations = locations[locations.apply(
            lambda row: check_accessibility(row, hands_on_activities_values,
                                            column_to_be_checked='hands_on_activities'),
            axis=1)]

        print(locations)

    print("location_count", len(locations))

    return locations


def sort_cycle_to_start_with_current_location(hamiltonian_cycle):
    # sort this cycle to always start with 0
    current_index = hamiltonian_cycle.index(0)
    hamiltonian_cycle = hamiltonian_cycle[current_index:] + hamiltonian_cycle[:current_index + 1]
    # remove duplicate nodes in the cycle
    hamiltonian_cycle = list(dict.fromkeys(hamiltonian_cycle))

    return hamiltonian_cycle


def find_shortest_path(shortest_path, filtered_data):
    # Shortest Path
    current_location = (shortest_path['latitude'], shortest_path['longitude'])
    G, hamiltonian_cycle = generate_graph(current_location, filtered_data)
    print(hamiltonian_cycle)

    # Sort
    hamiltonian_cycle = sort_cycle_to_start_with_current_location(hamiltonian_cycle)
    print(hamiltonian_cycle)

    # show all columns in the dataframe
    pd.set_option('display.max_columns', None)

    print(filtered_data)

    # Sort dataframe
    filtered_data = filtered_data.set_index('_id')
    filtered_data = filtered_data.reindex(hamiltonian_cycle)
    filtered_data = filtered_data.reset_index()

    # if the _id is 0 then add current location as latitude and longitude and name as "Current Location"
    filtered_data.loc[filtered_data['_id'] == 0, 'latitude'] = current_location[0]
    filtered_data.loc[filtered_data['_id'] == 0, 'longitude'] = current_location[1]
    filtered_data.loc[filtered_data['_id'] == 0, 'name'] = "Current Location"

    print(filtered_data)

    return filtered_data

#
# locations = pd.read_csv("data/locations.csv")
#
# # Not selected
# shortest_path = {
#     "user_id": "652b9e279c8deef2485bf90a",
#     "latitude": 6.91,
#     "longitude": 79.85,
#     "destination_id": "652b9d229c8deef2485bf8e8",
#     "distanceRadiusValue": 50.0,
#     "updatedData": {
#         "Time Restrictions": "0.00AM - 0.00PM",
#         "Accessibility": "Not selected",
#         "Historical Contexts": "Ancient Buddhist monastery",
#         "Hands-On Activities": "Photography, Sightseeing, Relaxing"
#     }
# }
#
# filtered_data = filter_data(shortest_path, locations)
#
# # keep only _id, name, latitude, longitude
# filtered_data = filtered_data[['_id', 'name', 'latitude', 'longitude']]
#
# filtered_data = find_shortest_path(shortest_path, filtered_data)
#

