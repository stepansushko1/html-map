import folium
import geopy
import math
from geopy.exc import GeocoderUnavailable
from geopy.extra.rate_limiter import RateLimiter


def write_file_to_txt(read_path: str, write_path: str):
    """ Convert .list file to .txt format """
    with open(read_path, "r", encoding='iso-8859-1') as file_1:

        for _ in range(14):
            next(file_1)
        our_text = file_1.read()

    with open(write_path, "w", encoding='iso-8859-1') as file_2:
        file_2.write(our_text)


def file_prepocessing(path: str):
    """ Processing of data. Bringing to next form: [film name, year, location, coords """
    with open(path, "r", encoding='iso-8859-1') as file:
        lst_of_movies = []
        i = 0
        for line in file:
            line = line.strip()
            line = line.split("\t")
            line = list(filter(None, line))  # remove ''

            if line[-1][0] == "(":  # for ( after the country
                del line[-1]

            line = " ".join(line)
            if "{" in line:                        # перевірка на лишні { } після року
                line = line.replace("{", '\t')
                line = line.replace("}", '\t')
                line = line.split("\t")
                del line[1]
                line = ' '.join(line)

            line = line.split(" ")
            line = list(filter(None, line))

            for i in range(len(line)):

                if line[i][0] == "(":

                    year = line[i]
                    film_name = " ".join(line[:i])
                    location = " ".join(line[i+1:])

                    if location[0] == "(":
                        location = location[location.find(")") + 1:]

                    line.clear()
                    line.append(film_name)
                    line.append(year[1:-1])  # year withou ()
                    line.append(location)

                    break

            lst_of_movies.append(line)

        return lst_of_movies


def find_year(films_lst: list, year: int):
    """ Filter list of films by given year """
    filtered_films_lst = [line for line in films_lst if line[1] == str(year)]

    return filtered_films_lst


def add_coords(filtered_lst):
    """ Find coordinates for list of films """
    for line in filtered_lst:
        try:
            location = line[2]

            location = location.split(", ")
            geolocator = geopy.Nominatim(user_agent="main.py")
            geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.05)
            adres = geolocator.geocode(location)

            if adres == None:
                location = location[1:]
                adres = geolocator.geocode(location)

                if adres == None:
                    location = location[1:]
                    adres = geolocator.geocode(location)

            coords = (float(adres.latitude), float(adres.longitude))

            line.append(coords)

        except GeocoderUnavailable:

            line.append("error")
    return filtered_lst


def coords_distance(my_coords: tuple, coords: tuple):
    """ Find distance between two coords """
    try:
        haversinus = (math.sin((math.pi / 180) * (my_coords[0] - coords[0])/2)**2 + math.cos((math.pi / 180)*my_coords[0])
                      * math.cos((math.pi / 180)*coords[0]) * math.sin((math.pi / 180)*(my_coords[1] - coords[1])/2)**2)
    except TypeError:
        haversinus = 100000

    try:
        distance = 6371.3 * 2 * math.asin(math.sqrt(haversinus))
    except ValueError:
        distance = 1000000

    return distance


def find_places(filtered_lst: list, my_coords: tuple):
    """ Find ten or less nearest places"""
    for i in range(len(filtered_lst)):
        filtered_lst[i].insert(0, coords_distance(
            my_coords, filtered_lst[i][3]))

    filtered_lst.sort()

    if len(filtered_lst) > 10:
        return filtered_lst[:10]

    return filtered_lst


def place_on_map(filtered_lst, my_coords):
    """ Generate a web-page with map and nearest movie places on it """
    my_map = folium.Map(tiles='OpenStreetMap', location=[
                        my_coords[0], my_coords[1]], zoom_start=5)

    fg = folium.FeatureGroup(name='Films map')

    lines = folium.FeatureGroup(name="Dots lines")

    for i in filtered_lst:
        if i[4][0] != "e":
            fg.add_child(folium.Marker(location=[i[4][0], i[4][1]],
                                       popup=i[1]))

            lines.add_child(folium.PolyLine([(i[4][0], i[4][1]), my_coords]))

    fg_pp = folium.FeatureGroup(name="Colored map")

    fg_pp.add_child(folium.GeoJson(data=open('world.json', 'r',
                                             encoding='utf-8-sig').read(),
                                   style_function=lambda x: {'fillColor': 'green'
                                                             if x['properties']['POP2005'] < 10000000
                                                             else 'orange' if 10000000 <= x['properties']['POP2005'] < 20000000
                                                             else 'red'}))

    my_map.add_child(lines)
    my_map.add_child(fg)
    my_map.add_child(fg_pp)
    my_map.add_child(folium.LayerControl())

    my_map.save("map.html")


def main():
    """ Main function that runs the module """
    year = int(input("Please, enter a year: "))
    latitude = float(input("Enter latitude: "))
    longitude = float(input("Enter longitude: "))
    my_coords = tuple([latitude, longitude])

    txt_file = "local.txt"

    films_with_correct_year = find_year(file_prepocessing("local.txt"), year)

    films_with_correct_year_coords = add_coords(films_with_correct_year)

    nearest_films = find_places(films_with_correct_year_coords, my_coords)

    places = place_on_map(nearest_films, my_coords)

    return places


if __name__ == "__main__":
    main()
