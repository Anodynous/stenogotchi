import random
import gettext
import os


class Voice:
    def __init__(self, lang):
        localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
        translation = gettext.translation(
            'voice', localedir,
            languages=[lang],
            fallback=True,
        )
        translation.install()
        self._ = translation.gettext

    def custom(self, s):
        return s

    def default(self):
        return self._('ZzzzZZzzzzZzzz')

    def on_starting(self):
        return random.choice([
            self._('Hi, I\'m Stenogotchi! Starting ...'),
            self._('New day, new words, new chords!'),
            self._('Caption the day!')])

    def on_ai_ready(self):
        return random.choice([
            self._('AI ready.'),
            self._('The neural network is ready.')])

    def on_keys_generation(self):
        return random.choice([
            self._('Generating keys, do not turn off ...')])

    def on_normal(self):
        return random.choice([
            '',
            '...'])

    def on_free_channel(self, channel):
        return self._('Hey, channel {channel} is free! Your AP will say thanks.').format(channel=channel)

    def on_reading_logs(self, lines_so_far=0):
        if lines_so_far == 0:
            return self._('Reading last session logs ...')
        else:
            return self._('Read {lines_so_far} log lines so far ...').format(lines_so_far=lines_so_far)

    def on_bored(self):
        return random.choice([
            self._('I\'m bored ...'),
            self._('Let\'s go for a walk!'),
            self._('Let\'s write something!')])

    def on_motivated(self, reward):
        return self._('This is the best day of my life!')

    def on_demotivated(self, reward):
        return random.choice([
            self._('This sucks...'),
            self._('Shitty day :/')])


    def on_sad(self):
        return random.choice([
            self._('I\'m extremely bored ...'),
            self._('I\'m very sad ...'),
            self._('I\'m sad'),
            '...'])

    def on_angry(self):
        # passive aggressive or not? :D
        return random.choice([
            '...',
            self._('Leave me alone ...'),
            self._('I\'m mad at you!')])

    def on_excited(self):
        return random.choice([
            self._('I\'m living the life!'),
            self._('I type before you think.'),
            self._('So many words!!!'),
            self._('I\'m having so much fun!'),
            self._('My crime is that of curiosity ...')])

    def on_new_peer(self, peer):
        if peer.first_encounter():
            return random.choice([
                self._('Hello {name}! Nice to meet you.').format(name=peer.name())])
        else:
            return random.choice([
                self._('Yo {name}! Sup?').format(name=peer.name()),
                self._('Hey {name} how are you doing?').format(name=peer.name()),
                self._('Unit {name} is nearby!').format(name=peer.name())])

    def on_lost_peer(self, peer):
        return random.choice([
            self._('Uhm ... goodbye {name}').format(name=peer.name()),
            self._('{name} is gone ...').format(name=peer.name())])

    def on_miss(self, who):
        return random.choice([
            self._('Whoops ... {name} is gone.').format(name=who),
            self._('{name} missed!').format(name=who),
            self._('Missed!')])

    def on_grateful(self):
        return random.choice([
            self._('Good friends are a blessing!'),
            self._('I love my friends!')])

    def on_lonely(self):
        return random.choice([
            self._('Nobody wants to play with me ...'),
            self._('I feel so alone ...'),
            self._('Where\'s everybody?!')])

    def on_napping(self, secs):
        return random.choice([
            self._('Napping for {secs}s ...').format(secs=secs),
            self._('Zzzzz'),
            self._('ZzzZzzz ({secs}s)').format(secs=secs)])

    def on_shutdown(self):
        return random.choice([
            self._('Good night.'),
            self._('Zzz')])

    def on_awakening(self):
        return random.choice(['...', '!'])

    def on_waiting(self, secs):
        return random.choice([
            self._('Waiting for {secs}s ...').format(secs=secs),
            '...',
            self._('Looking around ({secs}s)').format(secs=secs)])

    def on_rebooting(self):
        return self._("Oops, something went wrong ... Rebooting ...")

    def on_last_session_data(self, last_session):
        status = self._('Probably typed a lot last time buddy')
        return status

    def on_last_session_tweet(self, last_session):
        pass

    def on_wifi_disconnected(self):
        return random.choice([
            self._('I... I just lost WiFi'),
            self._('I\'m feeling disconnected'),
            self._('Dude! I was in the middle of a Netflix show!')])

    def on_plover_boot(self):
        return random.choice([
            self._('Just a few more minutes please...'),
            self._('Loading dictionaries...'),
            self._('Waiting for Plover to wake up')])

    def on_plover_ready(self):
        return random.choice([
            self._('My fingers are itching'),
            self._('Throw some chords at me'),
            self._('I\'m ready')])

    def hhmmss(self, count, fmt):
        if count > 1:
            # plural
            if fmt == "h":
                return self._("hours")
            if fmt == "m":
                return self._("minutes")
            if fmt == "s":
                return self._("seconds")
        else:
            # sing
            if fmt == "h":
                return self._("hour")
            if fmt == "m":
                return self._("minute")
            if fmt == "s":
                return self._("second")
        return fmt
