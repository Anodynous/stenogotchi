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
            self._('Wonder what we\'ll type next'),
            self._('Sure is cosy in here'),
            self._('We better not be writing any spam mail ...'),
            self._('I bet I\'m a great swimmer.'),
            self._('Used to know this Tama guy ... Real pest that one.'),
            self._('Did you know I\'m barely literate?'),
            self._('Hi'),
            self._('You\'re looking sharp today!'),
            self._('We\'re friends right? ... Best friends!'),
            '',
            '',
            '',
            '',
            '',
            '...'])

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
            self._('This sucks ...'),
            self._('Meh ...'),
            self._('What\'s even the point ...'),
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
            self._('I type before you think'),
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
            #self._('Napping for {secs}s ...').format(secs=secs),
            self._('Napping for a bit ...'),
            self._('Zzzzz'),
            self._('ZzzZzzz')])

    def on_shutdown(self):
        return random.choice([
            self._('Good night.'),
            self._('Zzz')])

    def on_awakening(self):
        return random.choice([
        '!',
        ''])

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

    def on_bt_connected(self, bthost_name):
        return random.choice([
            self._(f'Grabbed hold of {bthost_name} with my bluetooth tentacle'),
            self._(f'{bthost_name} is ready to receive'),
            self._(f'Sinking my tooth into {bthost_name}'),
            self._(f'Hi {bthost_name}, Let\'s team up!')])

    def on_bt_disconnected(self):
        return random.choice([
            self._('Lost connection to bluetooth host'),
            self._('Maybe it was a milk tooth and not bluetooth since it fell out ...'),
            self._('Need a new bluetooth connection buddy')])

    def on_wifi_connected(self, ssid, ip):
        return random.choice([
            self._(f'Found a town called {ssid}. I\'m gonna be known as {ip}'),
            self._(f'Connected to: {ssid} with ip: {ip}'),
            self._(f'Infiltrated {ssid} under the alias {ip}'),
            self._(f'Hit me up at {ssid} under {ip}')])

    
    def on_wifi_disconnected(self):
        return random.choice([
            self._('I... I just lost WiFi'),
            self._('I\'m feeling disconnected'),
            self._('Bruh, I was watching Netflix!')])

    def on_plover_boot(self):
        return random.choice([
            self._('Just waiting for Plover to pick up the phone now ...'),
            self._('Plover is loading dictionaries ...'),
            self._('Waiting for Plover to wake up')])

    def on_plover_ready(self):
        return random.choice([
            self._('My fingers are itching, let\'s type'),
            self._('Throw some chords at me bro'),
            self._('Plover is ready'),
            self._('Plover is finally dressed and ready to go'),
            self._('We are ready to go')])
    
    def on_wpm_record(self, wpm_top):
        if wpm_top < 100:
            return random.choice([
                self._('Keep up the good work!'),
                self._('You are getting quick!')])
        if wpm_top < 150:
            return random.choice([
                self._('Impressive!'),
                self._('You have left most qwerty users in the dust!')])
        elif wpm_top < 200:
            return random.choice([
                self._('Your fingers were a blur'),
                self._('Wow, I barely managed to keep up'),
                self._('Amazing!')])
        elif wpm_top < 250:
            return random.choice([
                self._('I can\'t keep up with you anymore'),
                self._('I can barely think that fast'),
                self._('Warp drive engaged!')])
        elif wpm_top < 300:
            return random.choice([
                self._('I\'m starting to think you\'re cheating!'),
                self._('Keep that up and your fingers will fly off')])
        else:
            return self._('Mark Kislingbury ... Is that you?!')
        
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
