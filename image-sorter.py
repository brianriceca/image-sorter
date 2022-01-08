#!/usr/bin/env python3

import PySimpleGUI as sg                        
import os.path
import PIL.Image
import sys
import base64
import json
import io

def convert_to_bytes(file_or_bytes, resize=None):
    '''
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (Union[str, bytes])
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    '''
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        try:
            img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = PIL.Image.open(dataBytesIO)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width*scale), int(cur_height*scale)), PIL.Image.ANTIALIAS)
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
            os.path.join(folder, f)) and f.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp"))]

if len(fnames) == 0:
  raise RuntimeError(f'No image files in {folder}')

with open('keys-and-dirs.json',encoding='utf-8') as f:
  directory_for_key = json.load(f)

set_of_keys = directory_for_key.keys()

sg.theme('DarkGreen')

imagepointer = 0

layout = [  [sg.Text(f"Simple image sorter: {fnames[imagepointer]}", key='-TITLE-')],
            [sg.Text('', size=(18,1), key='-FEEDBACK-')],
            [sg.Image(convert_to_bytes(fnames[imagepointer]),key='-IMAGE-')],
            [sg.Button('Prev'), sg.Button('Next'), sg.Button('Quit')] ]

window = sg.Window('Image Sorter', layout, resizable=True,
             return_keyboard_events=True, use_default_focus=False)

of = open('eventlog.txt','a')
                                                
while True:
  event, values = window.read()
  if event == sg.WIN_CLOSED or event == 'Quit' or event is None:
    break
  if len(event) == 1:
    window['-FEEDBACK-'].update(value=f"Got char {event}")
    continue
  if str(event).startswith('Right:') or event == 'Prev':
    imagepointer = imagepointer-1 if imagepointer > 0 else len(fnames)
    window['-FEEDBACK-'].update(f'imagepointer is {imagepointer}')
    window['-TITLE-'].update(f"Simple image sorter: {fnames[imagepointer]}")
    window['-IMAGE-'].update(data=convert_to_bytes(fnames[imagepointer]))
    continue
  if str(event).startswith('Left:') or event == 'Next':
    imagepointer = imagepointer+1 if imagepointer < len(fnames) else 0
    window['-FEEDBACK-'].update(f'imagepointer is {imagepointer}')
    window['-TITLE-'].update(f"Simple image sorter: {fnames[imagepointer]}")
    window['-IMAGE-'].update(data=convert_to_bytes(fnames[imagepointer]))
    continue
  window['-FEEDBACK-'].update(value=f"I got '{event}'")
  print(event , file=of)
#    if event in set_of_keys:
#      window['-FEEDBACK-'].update(value=f"You want me to move this to {directory_for_key[event]}")
#    else:
#      window['-FEEDBACK-'].update(value=f"I don't recognize {event}")

window.close()
of.close()
