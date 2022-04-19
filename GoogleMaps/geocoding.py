import googlemaps
import pandas as pd
from datetime import datetime
from multiprocessing.dummy import Pool
from tqdm import tqdm
from geopy.distance import geodesic
from itertools import combinations


class Geocoder:
    def __init__(self):
        self.counter = 0
        self.gmaps = googlemaps.Client(key="")
        self.failed_geocodes = []
        self.address_coordinate_map = {}
        self.route_distance_map = {}
        self.route_duration_map = {}

    def get_coordinate(self, address):
        try:
            location = self.gmaps.geocode(address)
            self.counter += 1

            lat = location[0]['geometry']['location']['lat']
            long = location[0]['geometry']['location']['lng']

            ret_coordinate = (lat, long)

            #self.address_coordinate_map[address] = ret_coordinate
            return tuple(lat, long)

        except(ValueError, Exception):
            self.failed_geocodes.append(address)
            return None

    def fetch_coordinate(self, address):
        try:
            return self.address_coordinate_map[address]
        except (ValueError, Exception):
            self.get_coordinate(address)
            try:
                return self.address_coordinate_map[address]
            except (KeyError, Exception):
                return None

    def thread_address_geocoding(self, address_list, threads):
        pool = Pool(threads)  # Number of concurrent threads
        for _ in tqdm(pool.imap_unordered(self.get_coordinate, address_list), total=len(address_list)):
            pass

    def get_google_distance(self, address_1, address_2):
        distance = self.gmaps.distance_matrix(address_1, address_2, mode='driving')
        self.counter += 1

        return distance

    def google_path_distance(self, input_tuple):
        route_id = input_tuple[0]
        stops_concat_string = input_tuple[1]

        distances_list = []
        durations_list = []
        stops_list = stops_concat_string.split('@^')
        if len(stops_list) == 1:
            self.route_distance_map[route_id] = None
            self.route_duration_map[route_id] = None
        else:
            for i in range(len(stops_list)):
                if i == 0:
                    continue

                stop_a = stops_list[i - 1]
                stop_b = stops_list[i]

                try:
                    distance_matrix_results = self.get_google_distance(stop_a, stop_b)
                    distance_value = distance_matrix_results["rows"][0]["elements"][0]["distance"]["value"]
                    duration_value = distance_matrix_results["rows"][0]["elements"][0]["duration"]["value"]

                    distances_list.append(distance_value)
                    durations_list.append(duration_value)
                except (ValueError, Exception):
                    print("failed distance calculation, skipping")
                    continue

            self.route_distance_map[route_id] = sum(distances_list)
            self.route_duration_map[route_id] = sum(durations_list)

    def thread_google_paths(self, stop_concat_string_list, threads):
        pool = Pool(threads)  # Number of concurrent threads
        for _ in tqdm(pool.imap_unordered(self.google_path_distance, stop_concat_string_list),
                      total=len(stop_concat_string_list)):
            pass


# ---------------------------

# Initialize geocoder class
# geocoder = Geocoder()

g_maps = googlemaps.Client(key='AIzaSyAitgFXGcX1HF3SaT-enAdljLV2jkf4lF8')

# Create function that produces coordinate
def get_coordinate(address):
    try:
        print(address)
        location = g_maps.geocode(address)

        lat = location[0]['geometry']['location']['lat']
        long = location[0]['geometry']['location']['lng']

        ret_coordinate = (lat, long)

        print(ret_coordinate)

        return ret_coordinate

    except(ValueError, Exception):
        return None


# Create function that produces geodesic distance between coordinates
def get_geodesic(c1, c2):
    distance = geodesic(c1,c2).km

    return distance


# create function that calculates google distance and duration
def get_google_distance(address_1, address_2):
    distance = g_maps.distance_matrix(address_1, address_2, mode='driving')

    return distance


# Create funtion that creates route data given two ids
def get_route_data(origin_id, destination_id, dataframe):
    origin_address = dataframe['Address'][origin_id]
    origin_borough = dataframe['Borough'][origin_id]
    origin_coordinate = eval(dataframe['Coordinate'][origin_id])
    destination_address = dataframe['Address'][destination_id]
    destination_borough = dataframe['Borough'][destination_id]
    destination_coordinate = eval(dataframe['Coordinate'][destination_id])
    geodesic_distance = get_geodesic(origin_coordinate, destination_coordinate)
    google_distance_object = get_google_distance(origin_address, destination_address)
    distance_value = google_distance_object["rows"][0]["elements"][0]["distance"]["value"]
    duration_value = google_distance_object["rows"][0]["elements"][0]["duration"]["value"]

    ret = {
        "origin_address": origin_address,
        "origin_borough": origin_borough,
        "origin_coordinate": origin_coordinate,
        "destination_address": destination_address,
        "destination_borough": destination_borough,
        "is_same_borough": origin_borough == destination_borough,
        "destination_coordinate": destination_coordinate,
        "geodesic_distance": geodesic_distance,
        "google_distance": distance_value,
        "google_duration": duration_value
    }

    return ret


# Load and process data
data = pd.read_csv("post_office_coords.csv", index_col=False)


# create list of id pairs
ids = list(data.index)
route_combinations = list(combinations(ids, 2))

# for each id pair, generate route data and store in list
routes = []
i = 1
for combination in route_combinations:
    print("{}/{}".format(i,len(route_combinations)))
    i += 1
    id1 = combination[0]
    id2 = combination[1]

    try:
        route_data = get_route_data(id1, id2, data)
        routes.append(route_data)
    except (ValueError, Exception):
        continue


df = pd.DataFrame(routes)

df.to_csv("route_data.csv")


