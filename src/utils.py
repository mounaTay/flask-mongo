import pandas as pd
import pymongo
import requests
import os


class DB:

    def __init__(self):
        """
        Initialize DB to connect with mongo client and a database
        """
        import gridfs
        self.client = pymongo.MongoClient(os.getenv("MONGO_CLIENT", "mongodb://172.17.0.2:27017"))
        self.db = self.client[os.getenv("MONGO_DATABASE", "demo")]
        self.fs = gridfs.GridFS(self.db)

    def read(self, collection, id: str = None) -> pymongo.cursor.Cursor:
        """
        read records from a collection stored in mongodb
        :param collection: collection name to query from
        :param id: optional parameter to filter records
        :return: a cursor to mongo records
        """
        if id is not None:
            return self.db[collection].find({"_id": id})
        else:
            return self.db[collection].find()

    def write(self, collection, data) -> None:
        """
        write records of data to a mongodb collection
        :param collection: collection that stores records
        :param data: data to write in the mongodb collection
        :return: status of inserting data into collection
        """
        return self.db[collection].insert_one(data)


class PersonDetails(DB):
    id_counter = 0  # class attribute, used to assign ids to every new person added to the database

    def __init__(self, url: str = "https://thispersondoesnotexist.com/image", input: str = "babynames-clean.csv"):
        super().__init__()
        self.url = url
        self.input = input

    def __call__(self, *args, **kwargs):
        self.name = self.assign_name()
        self.my_json = {"_id": str(PersonDetails.id_counter), "name": self.name}
        PersonDetails.id_counter += 1
        self.download_file()
        self.my_json["faces"] = self.face_recognition()["faces"]
        self.my_json["gender"] = self.genderize()
        self.my_json["age"] = self.agify()
        self.my_json["nationality"] = self.nationalize()

        return self.write("person", self.my_json)

    def download_file(self) -> None:
        """
        Downloads a file from a given url and saves it locally
        :return: does not return
        """

        r = requests.get(self.url)
        with open(f"{self.name}.jpeg", 'wb') as f:
            self.my_json["image"] = self.fs.put(r.content, filename=f"{self.name}.jpeg")
            f.write(r.content)

    def assign_name(self) -> str:
        """
        reads a csv using pandas and get a sample row out of it
        :return: a random name from the csv
        """
        return pd.read_csv(self.input, names=["name", "gender"], index_col=False)["name"].sample().values[0]

    def face_recognition(self):
        """
        Query faceplusplus api for face recognition
        :return: json response from the face recognition api
        """
        url = "https://faceplusplus-faceplusplus.p.rapidapi.com/facepp/v3/detect"

        querystring = {
            "image_url": self.url,
            "api_key": os.getenv("FACEPLUSPLUS_API_KEY", ""),
            "api_secret": os.getenv("FACEPLUSPLUS_API_SECRET", "")
        }

        headers = {
            "X-RapidAPI-Key": os.getenv("RapidAPI_KEY", ""),
            "X-RapidAPI-Host": "faceplusplus-faceplusplus.p.rapidapi.com"
        }

        return requests.request("POST", url, headers=headers, params=querystring).json()

    def genderize(self) -> str:
        """
        get gender from genderize api based on the person's name
        :return: the person's gender
        """
        return requests.get(f"https://api.genderize.io?name={self.name}").json()["gender"]

    def agify(self) -> str:
        """
        get age from agify api based on the person's name
        :return: the person's age
        """
        return requests.get(f"https://api.agify.io?name={self.name}").json()["age"]

    def nationalize(self) -> str:
        """
        get nationality from nationalize api based on the person's name
        :return: the person's nationality/country id
        """
        countries = requests.get(f"https://api.nationalize.io?name={self.name}").json()["country"]
        countries.sort(key=lambda x: x["probability"], reverse=True)
        return countries[0]["country_id"]


if __name__ == "__main__":
    url = "https://thispersondoesnotexist.com/image"
    input = "babynames-clean.csv"
    person_details = PersonDetails(url, input)
    person_details()
    person_details.client.close()
