import airtable
from settings import atb_token


class EventRepository:
    airtable = airtable.Airtable('lfg', 'events', atb_token)

    def add_event(self, name, slots, date, tg_post_id, tg, disc):
        self.airtable.insert({'tg_post_id': int(tg_post_id),
                              'slots': int(slots),
                              'date': date.strftime("%Y-%m-%d, %H:%M"),
                              'name': name,
                              'tg': tg,
                              'disc': disc})

    def delete(self, record):
        self.airtable.delete(record_id=record)

    def get_event(self, tg_post_id: str) -> dict:
        data = self.airtable.search('tg_post_id', tg_post_id)
        if data:
            return data[0]


class ParticipantRepository:
    airtable = airtable.Airtable('lfg', 'participants', atb_token)

    def add_participant(self, event_id, tg, tg_post_id):
        self.airtable.insert({
            'event_id': [event_id],
            'tg': tg,
            'tg_post_id': tg_post_id
        })

    def del_participant(self, record):
        self.airtable.delete(record_id=record)

    # def del_participant_by_id(self, tg_post_id):
    #    self.airtable.delete_by_field('tg_post_id', tg_post_id)

    def get_event_participants(self, tg_post_id: str) -> dict:
        data = self.airtable.search('tg_post_id', tg_post_id)
        if data:
            return data


class UserRepository:
    airtable = airtable.Airtable('lfg', 'users', atb_token)

    def add_user(self, tg, tg_chat_id):
        self.airtable.insert({
            'tg': tg,
            'tg_chat_id': tg_chat_id,
        })

    def get_user(self, tg: str) -> dict:
        try:
            data = self.airtable.search('tg', tg)
        except:
            return None
        if data:
            return data[0]

    def toggle_mute(self, tg, mute):
        user = self.get_user(tg)
        self.airtable.update(record_id=user.get("id"), fields={
            'mute': mute
        })
