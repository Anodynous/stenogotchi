from stenogotchi.ui.hw.waveshare2 import WaveshareV2
from stenogotchi.ui.hw.waveshare3 import WaveshareV3

def display_for(config):
    # config has been normalized already in utils.load_config
    if config['ui']['display']['type'] == 'waveshare_2':
        return WaveshareV2(config)
    elif config['ui']['display']['type'] == 'waveshare_3':
        return WaveshareV3(config)
    else:
        print("no display specified")