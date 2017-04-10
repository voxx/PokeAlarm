import requests

# THIS SCRIPT IS FOR TESTING TO MAKE SURE PA IS WORKING
# IT SHOULD TOTALLY NOT BE USED TO FAKE WEBHOOKS
# THAT WOULD BE TOTALLY BAD AND MEAN THING TO DO
if __name__ == '__main__':
    IP = "127.0.0.1"
    PORT = "4000"
    PAYLOAD = {
        "type": "pokemon",
        "message": {
            "encounter_id": 1, # Change this after each webhook
            "spawnpoint_id": 1,
            "pokemon_id": 151, # Number of the pokemon
            "latitude": 42.284343,
            "longitude":  -85.5944494,
            "disappear_time": 1491091200, # April 2nd, 2017
            "last_modified_time": 1386668800,
            "time_until_hidden_ms": 5000,
            "individual_attack": 15,
            "individual_defense": 15,
            "individual_stamina": 15,
            "move_1": "222",
            "move_2": "226",
            "height": "4.0",
            "weight": ".41",
            "gender": "1"
        }
    }

    print("SENDING WBEHOOK TO http://{}:{}".format(IP, PORT) )
    r = requests.post('http://{}:{}'.format(IP, PORT), json=PAYLOAD, )
    if r.status_code == 200:
        print "SENT SUCCESSFULLY - PA SHOULD BE WORKING CORRECTLY"
    else:
print "SOME ERROR HAPPENED: DID NOT RECEIVE 200"
