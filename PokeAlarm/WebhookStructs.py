# Standard Library Imports
from datetime import datetime
import logging
import multiprocessing
import traceback
# 3rd Party Imports
# Local Imports
from Utils import get_gmaps_link

log = logging.getLogger('Structures')

################################################## Webhook Standards  ##################################################


# RocketMap Standards
class RocketMap:
    def __init__(self):
        raise NotImplementedError("This is a static class not meant to be initiated")

    @staticmethod
    def make_object(data):
        try:
            kind = data.get('type')
            if kind == 'pokemon':
                return RocketMap.pokemon(data.get('message'))
            elif data['type'] == 'pokestop':
                return RocketMap.pokestop(data.get('message'))
            elif data['type'] == 'gym' or data['type'] == 'gym_details':
                return RocketMap.gym(data.get('message'))
            elif data['type'] in ['captcha', 'scheduler']:  # Unsupported Webhooks
                log.debug("{} webhook received. This captcha is not yet supported at this time. ")
            else:
                log.error("Invalid type specified ({}). Are you using the correct map type?".format(kind))
        except Exception as e:
            log.error("Encountered error while processing webhook ({}: {})".format(type(e).__name__, e))
            log.debug("Stack trace: \n {}".format(traceback.format_exc()))
        return None

    @staticmethod
    def pokemon(data):
        log.debug("Converting to pokemon: \n {}".format(data))

        # Check optional data
        move_1_id, move_2_id = data.get('move_1'), data.get('move_2')
        atk, def_, sta = data.get('individual_attack'), data.get('individual_defense'), data.get('individual_stamina')
        height, weight, gender = data.get('height'), data.get('weight'), data.get('gender')

        pkmn = {
            'type': "pokemon",
            'id': data['encounter_id'],
            'pkmn_id': int(data['pokemon_id']),
            'disappear_time': datetime.utcfromtimestamp(data['disappear_time']),
            'lat': float(data['latitude']),
            'lng': float(data['longitude']),
            'move_1_id': int(move_1_id) if move_1_id is not None else 'unkn',
            'move_2_id': int(move_2_id) if move_2_id is not None else 'unkn',
            'atk': int(atk) if atk is not None else 'unkn',
            'def': int(def_) if def_ is not None else 'unkn',
            'sta': int(sta) if sta is not None else 'unkn',
            'height': float(height) if height is not None else '?',
            'weight': float(weight) if weight is not None else '?',
            'gender': int(gender) if gender is not None else '?'
        }
        pkmn['gmaps'] = get_gmaps_link(pkmn['lat'], pkmn['lng'])
        if atk is None or def_ is None or sta is None:
            pkmn['iv'] = 'unkn'
        else:
            pkmn['iv'] = float(((atk + def_ + sta) * 100) / float(45))

        return pkmn

    @staticmethod
    def pokestop(data):
        log.debug("Converting to pokestop: \n {}".format(data))
        if data.get('lure_expiration') is None:
            log.debug("Un-lured pokestop... ignoring.")
            return None
        stop = {
            'type': "pokestop",
            'id': data['pokestop_id'],
            'expire_time':  datetime.utcfromtimestamp(data['lure_expiration']),
            'lat': float(data['latitude']),
            'lng': float(data['longitude'])
        }
        stop['gmaps'] = get_gmaps_link(stop['lat'], stop['lng'])
        return stop

    @staticmethod
    def gym(data):
        log.debug("Converting to gym: \n {}".format(data))
        gym = {
            'type': "gym",
            'id': data.get('gym_id',  data.get('id')),
            "team_id": int(data.get('team_id',  data.get('team'))),
            "points": str(data.get('gym_points')),
            "guard_pkmn_id": data.get('guard_pokemon_id'),
            'lat': float(data['latitude']),
            'lng': float(data['longitude'])
        }
        gym['gmaps'] = get_gmaps_link(gym['lat'], gym['lng'])
        return gym
########################################################################################################################


class Geofence(object):

    # Expects points to be
    def __init__(self, name, points):
        self.__name = name
        self.__points = points

        self.__min_x = points[0][0]
        self.__max_x = points[0][0]
        self.__min_y = points[0][1]
        self.__max_y = points[0][1]

        for p in points:
            self.__min_x = min(p[0], self.__min_x)
            self.__max_x = max(p[0], self.__max_x)
            self.__min_y = min(p[1], self.__min_y)
            self.__max_y = max(p[1], self.__max_y)

    def contains(self, x, y):
        # Quick check the boundary box of the entire polygon
        if self.__max_x < x or x < self.__min_x or self.__max_y < y or y < self.__min_y:
            return False

        inside = False
        p1x, p1y = self.__points[0]
        n = len(self.__points)
        for i in range(1, n+1):
            p2x, p2y = self.__points[i % n]
            if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def get_name(self):
        return self.__name


# Class to allow optimization of waiting requests (not process safe)
class QueueSet(object):
    def __init__(self):
        self.__queue = multiprocessing.Queue()
        self.__lock = multiprocessing.Lock()
        self.__data_set = {}

    # Add or update an object to the QueueSet
    def add(self, id_, obj):
        self.__lock.acquire()
        try:
            if id_ not in self.__data_set:
                self.__queue.put(id_)
            self.__data_set[id_] = obj  # Update info incase it had changed
        except Exception as e:
            log.error("QueueSet error encountered in add: \n {}".format(e))
        finally:
            self.__lock.release()

    # Remove the next item in line
    def remove_next(self):
        self.__lock.acquire()
        data = None
        try:
            id_ = self.__queue.get(block=True)  # get the next id
            data = self.__data_set[id_]  # extract the relevant data
            del self.__data_set[id_]  # remove the id from the set
        except Exception as e:
            log.error("QueueSet error encountered in remove: \n {}".format(e))
        finally:
            self.__lock.release()
        return data
