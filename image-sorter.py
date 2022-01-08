#!/usr/bin/env python3

import PySimpleGUI as sg                        
import os.path
import PIL.Image as pilimage
import sys
import base64
import json
import io

default_size = (600,600)
script_folder = os.path.dirname(os.path.realpath(__file__))

image_types = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")

def convert_to_bytes(file_or_bytes, resize=None, dirpath=None):
    '''
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (Union[str, bytes])
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    :param dirpath: directory path to file
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    '''
    if isinstance(file_or_bytes, str):
        if dirpath is None:
            img = pilimage.open(file_or_bytes)
        else:
            img = pilimage.open(os.path.join(dirpath,file_or_bytes))
    else:
        try:
            img = pilimage.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = pilimage.open(dataBytesIO)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width*scale), int(cur_height*scale)), pilimage.ANTIALIAS)
    with io.BytesIO() as bio:
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()

if len(sys.argv) > 1:
  folder = sys.argv[1]
else:
  folder = '.'

try:
  file_list = os.listdir(folder)         # get list of files in folder
except:
  file_list = []

fnames = [f for f in file_list if os.path.isfile(
            os.path.join(folder, f)) and f.lower().endswith(image_types)
            and not f.startswith('.')
          ]

def _fnames(i):
  if i >= 0 and i < len(fnames):
    return fnames[i]
  else:
    return os.path.join(script_folder,'no_image.png')
    
def dict_raise_on_duplicates(ordered_pairs):
  """Reject duplicate keys."""
  d = {}
  for k, v in ordered_pairs:
    if k in d:
      raise ValueError("duplicate key: %r" % (k,))
    else:
      d[k] = v
  return d

key_config_file = os.path.join(script_folder,'keys-and-dirs.json')
if os.path.exists(key_config_file):
  with open(os.path.join(script_folder,'keys-and-dirs.json'),encoding='utf-8') as f:
    directory_for_key = json.load(f,object_pairs_hook=dict_raise_on_duplicates)

if len(directory_for_key) == 0:
  raise RuntimeError(f'No action keys defined')

if 'q' in directory_for_key:
  raise RuntimeError(f'Sorry, q means quit')

if len(directory_for_key.keys()) != len(set(directory_for_key.keys())):
  raise RuntimeError(f'Duplicate key(s) defined')
  
set_of_keys = set(directory_for_key.keys())

sg.theme('DarkGreen')

imagepointer = 0

layout = [  [sg.Text(f"Simple image sorter: {_fnames(imagepointer)}", key='-TITLE-')],
            [sg.Text('', size=(50,1), key='-FEEDBACK-')],
            [sg.Image(convert_to_bytes(_fnames(imagepointer),resize=default_size,dirpath=folder),key='-IMAGE-')],
            [sg.Button('Prev'), sg.Button('Next'), sg.Button('Delete',button_color=('#FFFFFF','#FF0000')),sg.Button('Quit')] ]

window = sg.Window('Image Sorter', layout, resizable=True,
             return_keyboard_events=True, use_default_focus=False)

of = open('eventlog.txt','a')
                                                
while True:
  event, values = window.read()
  if (event == sg.WIN_CLOSED or event is None or
      event == 'Quit' or event.startswith('q')):
    break
  window['-FEEDBACK-'].update(value=f"Got event '{event}'")
  if str(event).startswith('Left:') or event == 'Prev':
    imagepointer = imagepointer-1 if imagepointer > 0 else len(fnames)-1
    window['-FEEDBACK-'].update(f'imagepointer is {imagepointer}')
    window['-TITLE-'].update(f"Simple image sorter: {_fnames(imagepointer)}")
    window['-IMAGE-'].update(data=convert_to_bytes(_fnames(imagepointer),resize=default_size,dirpath=folder))
    continue
  if str(event).startswith('Right:') or event == 'Next':
    imagepointer = imagepointer+1 if imagepointer < len(fnames)-1 else 0
    window['-FEEDBACK-'].update(f'imagepointer is {imagepointer}')
    window['-TITLE-'].update(f"Simple image sorter: {_fnames(imagepointer)}")
    window['-IMAGE-'].update(data=convert_to_bytes(_fnames(imagepointer),resize=default_size,dirpath=folder))
    continue
  if event in set_of_keys:
    window['-FEEDBACK-'].update(value=f"You want to move this to '{directory_for_key[event]}'")
