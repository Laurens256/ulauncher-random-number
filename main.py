from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

import random
import re

# function returns a string because of the way Python handles floats
# we want to preserve precision of the number, so we return a string since Python automatically removes trailing zeros from floats
def get_random_number(lower, upper):
    lower_int = string_to_num(lower)
    upper_int = string_to_num(upper)
    # if either number is a float, we generate a float with the same precision as the highest precision number
    if isinstance(lower_int, float) or isinstance(upper_int, float):       
        lower_precision = calculate_precision(lower)
        upper_precision = calculate_precision(upper)
        precision = max(lower_precision, upper_precision)

        random_num_string = "{:.{prec}f}".format(random.uniform(lower_int, upper_int), prec=precision)

        return random_num_string
    else:
        return str(random.randint(lower_int, upper_int))
    

# function to calculate precision of a number (number of decimal places)
def calculate_precision(string):
    split_value = string.replace(',', '.').split('.')
    return len(split_value[1]) if len(split_value) > 1 else 0


def string_to_num(string):
    string = string.replace(',', '.')
    
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            raise ValueError
        
# lower and upper bounds are passed as strings, to preserve precision
# python automatically removes trailing zeros from floats, so we keep them as strings
def render_result(lower, upper):
    random_number = get_random_number(lower, upper)
    data = {'lower_range': lower, 'upper_range': upper}        

    return RenderResultListAction([
        ExtensionResultItem(icon='images/icon.png',
                            name=f'{random_number}',
                            description=f'Random number between {lower} and {upper} is {random_number}',
                            on_enter=CopyToClipboardAction(str(random_number))),
        ExtensionResultItem(icon='images/icon.png',
                            name='Reroll',
                            description='Reroll with the same range',
                            on_enter=ExtensionCustomAction(data, keep_app_open=True))
        ])

def render_error(err_name, err_description):
    return RenderResultListAction([
        ExtensionResultItem(icon='images/icon.png',
                            name=err_name,
                            description=err_description,
                            on_enter=HideWindowAction())
    ])

# function to get range from user input
# when None is returned, default value from preferences is used
def get_range(arguments):
    # remove any trailing or leading characters that are not numbers
    arguments = re.sub(r'^\D+|\D+$', '', arguments)

    if not arguments:
        return { 'lower': None, 'upper': None }
    
    try:
        string_to_num(arguments)
        return { 'lower': None, 'upper': arguments }
    except ValueError:
        pass

    try:
        lower, upper = re.split(r'[\s/|:;~-]', arguments)
        string_to_num(lower)
        string_to_num(upper)
        return { 'lower': lower, 'upper': upper }
    except ValueError:
        raise ValueError



class RandomNumberExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        range_obj = get_range(event.get_argument() or '')

        try:
            default_range = get_range(extension.preferences.get('default_range'))
            default_lower_range, default_upper_range = default_range['lower'], default_range['upper']

            lower_range = range_obj['lower'] or default_lower_range
            upper_range = range_obj['upper'] or default_upper_range

            if not isinstance(lower_range, str) or not isinstance(upper_range, str):
                raise AttributeError
            
            lower_range_num = string_to_num(lower_range)
            upper_range_num = string_to_num(upper_range)

        except ValueError:
            return render_error('Invalid range', 'Please use numbers only')
        
        except AttributeError:
            return render_error('Invalid range', 'Please choose a range or set a default range')
        
        if upper_range_num <= lower_range_num:
            return render_error('Invalid range', 'Upper range must be greater than lower range')
            
        return render_result(lower_range, upper_range)
    

class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        data = event.get_data()
        return render_result(data['lower_range'], data['upper_range'])


if __name__ == '__main__':
    RandomNumberExtension().run()
    