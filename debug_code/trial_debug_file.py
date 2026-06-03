### This is a trial debug file that you will solve on your own ###
from typing import List, Dict

passenger_data = [{"passenger_id":1, "sex":"M", "height":175},
              {"passenger_id":2, "sex":"F", "height":180},
              {"passenger_id":3, "sex":"M", "height":177},
              {"passenger_id":4,"sex":"F", "height":167},
              {"passenger_id":5, "sex":"F", "height":160},
              {"passenger_id":6, "sex":"M", "height":190},
              {"passenger_id":7, "sex":"F", "height":159},
              {"passenger_id":8, "sex":"M", "height":181}]

class Passenger:
    def __init__(self, passenger_id, sex, height):
        self.passenger_id = passenger_id
        self.sex = sex
        self.height = height

class Passengers:
    def __init__(self):
        self.passengers = []
        self.nr_passengers = None
        self.avg_height_passengers = None
        self.demographic = None
        self.no_flight_list = [1,3,5,6]

    def populate_passengers(self, passenger_data:List[Dict[str, int]]):
        """
        Populate passenger list with passenger objects using the data above
        """
        for pas in passenger_dat:
            passenger = Passenger(passenger_id=pas["passenger_id"], sex=pas["sex"], height=pas["height"])
            self.passengers.append(passenger)

        return self.passengers

    def calculate_avg_height(self):
        total_height = 0

        if not self.passengers:
            return None

        for pas in self.passengers:
            total_height+=pas.height

        print(total_height/len(self.passengers))

    def calculate_demographic(self):
        male = 0
        female = 0

        for pas in self.passengers:
            if pas.sex == "M":
                male += 1
            else:
                female += 1

        if male < female:
            return "Male", male

        return "Female", female

    def check_no_flight_list(self):
        no_flight = []

        for i, pas in enumerate(self.passengers):
            if pas.passenger_id in self.no_flight_list:
                no_flight.add(pas.passenger_id)
                self.passengers.pop(i)

        return no_flight, list(pas.passenger_id for pas in self.passengers)

if __name__ == "__main__":
    Passengers = Passengers()
    Passengers.populate_passengers(passenger_data)

    avg_height = Passengers.calculate_avg_height()
    demographic, nr = Passengers.calculate_demographic()
    no_flight, flight = Passengers.check_no_flight_list()

    print(f"Average height: {avg_height}")
    print(f"Predominant demographic: {demographic} ({nr})")
    print(f"Passengers on no flight list: {no_flight}")
    print(f"Passengers allowed to fly: {flight}")