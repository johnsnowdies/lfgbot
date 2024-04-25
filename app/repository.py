from pymongo import MongoClient

client = MongoClient('mongo')
db = client['lfg']


class EventRepository:
    def add_event(self, name, slots, date, tg_post_id, tg, disc):
        events_collection = db['events']
        events_collection.insert_one({
            'tg_post_id': int(tg_post_id),
            'slots': int(slots),
            'date': date.strftime("%Y-%m-%d, %H:%M"),
            'name': name,
            'tg': tg,
            'disc': disc
        })

    def delete(self, event_id):
        events_collection = db['events']
        events_collection.delete_one({'_id': event_id})

    def get_event(self, tg_post_id: str) -> dict:
        events_collection = db['events']
        return events_collection.find_one({'tg_post_id': tg_post_id})


class ParticipantRepository:
    def add_participant(self, event_id, tg, tg_post_id):
        participants_collection = db['participants']
        participants_collection.insert_one({
            'event_id': event_id,
            'tg': tg,
            'tg_post_id': tg_post_id
        })

    def del_participant(self, participant_id):
        participants_collection = db['participants']
        participants_collection.delete_one({'_id': participant_id})

    def get_event_participants(self, tg_post_id: str) -> dict:
        participants_collection = db['participants']
        return list(participants_collection.find({'tg_post_id': tg_post_id}))


class UserRepository:
    def add_user(self, tg, tg_chat_id):
        users_collection = db['users']
        users_collection.insert_one({
            'tg': tg,
            'tg_chat_id': tg_chat_id,
        })

    def get_user(self, tg: str) -> dict:
        users_collection = db['users']
        return users_collection.find_one({'tg': tg})

    def toggle_mute(self, tg, mute):
        users_collection = db['users']
        user = self.get_user(tg)
        if user:
            users_collection.update_one({'_id': user['_id']}, {'$set': {'mute': mute}})
