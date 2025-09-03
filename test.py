from pymongo import MongoClient

MONGO_URI = "mongodb+srv://<user>:<password>@cluster0.telweny.mongodb.net/?retryWrites=true&w=majority&tls=true"
client = MongoClient(MONGO_URI)
print(client.server_info())
