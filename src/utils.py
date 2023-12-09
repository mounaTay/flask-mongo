import pandas as pd
import pymongo
import requests
import os
from bson.objectid import ObjectId
from security import safe_requests


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
        if id is not None and ObjectId.is_valid(id):
            return self.db[collection].find({"_id": ObjectId(id)})
        elif id is not None:
            return []
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
    def __init__(self, url: str = "https://thispersondoesnotexist.com/image", input: str = "babynames-clean.csv"):
        """
        Initialize a person and define the url to get the person's image and the input file to assign a random name
        the class initializes the DB class to be able to use the read/write function of the database
        :param url: define the source api for getting the person's image
        :param input: csv file to assign a random name to the person
        """
        super().__init__()
        self.url = url
        self.input = input

    def __call__(self, *args, **kwargs):
        """
        workflow to use each time we call the person details class
        """
        self.name = self.assign_name()
        self.my_json = {"name": self.name}
        self.download_file()
        self.my_json["faces"] = self.face_recognition()
        self.my_json["gender"] = self.genderize()
        self.my_json["age"] = self.agify()
        self.my_json["nationality"] = self.nationalize()
        self.write("person", self.my_json)

    def assign_name(self) -> str:
        """
        reads a csv using pandas and get a sample row out of it
        :return: a random name from the csv
        """
        return pd.read_csv(self.input, names=["name", "gender"], index_col=False)["name"].sample().values[0]

    def download_file(self) -> None:
        """
        Downloads a file from a given url and saves it locally
        :return: does not return
        """

        response = safe_requests.get(self.url)
        if response.ok:
            with open(f"{self.name}.jpeg", 'wb') as f:
                content = response.content
                self.my_json["image"] = self.fs.put(content, filename=f"{self.name}.jpeg")
                f.write(content)
        else:
            response.raise_for_status()

    def face_recognition(self) -> str:
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
        response = requests.request("POST", url, headers=headers, params=querystring)
        if response.ok:
            return response.json()["faces"]
        else:
            response.raise_for_status()

    def genderize(self) -> str:
        """
        get gender from genderize api based on the person's name
        :return: the person's gender
        """
        response = safe_requests.get(f"https://api.genderize.io?name={self.name}")
        if response.ok:
            return response.json()["gender"]
        else:
            response.raise_for_status()

    def agify(self) -> str:
        """
        get age from agify api based on the person's name
        :return: the person's age
        """
        response = safe_requests.get(f"https://api.agify.io?name={self.name}")
        if response.ok:
            return response.json()["age"]
        else:
            response.raise_for_status()

    def nationalize(self) -> str:
        """
        get nationality from nationalize api based on the person's name
        :return: the person's nationality/country id or None in case of failure
        """
        response = safe_requests.get(f"https://api.nationalize.io?name={self.name}")
        if response.ok:
            countries = response.json()["country"]
            countries.sort(key=lambda x: x["probability"], reverse=True)
            return countries[0]["country_id"]
        else:
            response.raise_for_status()


if __name__ == "__main__":
    url = "https://thispersondoesnotexist.com/image"
    input = "babynames-clean.csv"
    person_details = PersonDetails(url, input)
    person_details()
    person_details.client.close()
