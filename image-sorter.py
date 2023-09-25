#!/usr/bin/env python3

import PySimpleGUI as sg                        
import os
import subprocess
import shutil
import PIL.Image as pilimage
import sys
import base64
import json
import io
import tempfile
import argparse

key_config_base_filename = 'keys-and-dirs.json'
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--configfile')
parser.add_argument('indir')

args = parser.parse_args()
if args.configfile:
  key_config_base_filename = args.configfile
source_folder = args.indir
print(f'key_config_base_filename is {key_config_base_filename}')

default_size = (600,600)
script_install_loc = os.path.dirname(os.path.realpath(__file__))
trashdir = os.path.join(os.environ.get('HOME'),'.trash')

image_types = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")
video_types = (".mp4")

if not (os.path.exists(source_folder) and os.path.isdir(source_folder)):
  print(f'{sys.argv[0]}: usage: source folder {source_folder} is bad')
  sys.exit(3)

key_config_file = os.path.join(script_install_loc,key_config_base_filename)

def convert_to_bytes(fname, resize=None, dirpath=None):
    '''
    Will convert into bytes and optionally resize an image that is a file 
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param fname: a string filename 
    :type fname:  str
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    :param dirpath: directory path to file
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    '''
    if isinstance(fname, str):
      # first, is it a video file? If so, we need to point instead to the
      # video sample frame, generating it if need be
      if fname.endswith(video_types):
        sampleframe_name = "." + fname + ".png"       
        if dirpath is None:
          sampleframe_name = os.path.join(".",sampleframe_name)
        else:
          sampleframe_name = os.path.join(dirpath,sampleframe_name)
        if not os.path.exists(sampleframe_name):
          print(f"about to generate {sampleframe_name}")
          print('ffmpeg -i \'' + fname + '\'' + " -vf select='eq(n\,30)' " +
                    '\'' + sampleframe_name + '\' >/tmp/out.$$ 2>&1')
          with open('/tmp/ffmpeg.out.' + str(os.getpid()),"w") as logfile:
            subprocess.run(['ffmpeg',
                            '-i', 
                            fname, 
                            "-vf",
                            "select='eq(n\,30)'",
                            sampleframe_name],
                          stdout=logfile, stderr=subprocess.STDOUT)
          print(f"generated {sampleframe_name}")
        fname = sampleframe_name              
        img = pilimage.open(os.path.join(dirpath,fname))
      else:
        if dirpath is None:
          fname = os.path.join(".",fname)
        else:
          fname = os.path.join(dirpath,fname)
        img = pilimage.open(os.path.join(dirpath,fname))
    else:
        raise ValueException;

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width*scale), int(cur_height*scale)), pilimage.LANCZOS)
    with io.BytesIO() as bio:
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()

try:
  file_list = os.listdir(source_folder)         # get list of files in source_folder
except:
  file_list = []

fnames = [f for f in file_list if os.path.isfile(
            os.path.join(source_folder, f)) and 
            (f.lower().endswith(image_types) or f.lower().endswith(video_types))
            and not f.startswith('.')
          ]

fnames.sort()

def _fnames(i):
  if i >= 0 and i < len(fnames):
    return fnames[i]
  else:
    return os.path.join(script_install_loc,'no_image.png')
    
def dict_raise_on_duplicates(ordered_pairs):
  """Reject duplicate keys."""
  d = {}
  for k, v in ordered_pairs:
    if k in d:
      raise ValueError("duplicate key: %r" % (k,))
    else:
      d[k] = v
  return d

if os.path.exists(key_config_file):
  with open(os.path.join(script_install_loc,key_config_base_filename),encoding='utf-8') as f:
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

keyhelp1 = ' '.join([f'{k}:{os.path.basename(directory_for_key[k])}' for k in sorted(directory_for_key.keys()) if k.islower()])
keyhelp2 = ' '.join([f'{k}:{os.path.basename(directory_for_key[k])}' for k in sorted(directory_for_key.keys()) if not k.islower()])
keyhelp_width = max(len(keyhelp1),len(keyhelp2))

layout = [  [sg.Text(f"Simple image sorter: {_fnames(imagepointer)} [{imagepointer}/{len(fnames)}]", key='-TITLE-')],
            [sg.Text(keyhelp1, size=(keyhelp_width,1), key='-KEYHELP1-')],
            [sg.Text(keyhelp2, size=(keyhelp_width,1), key='-KEYHELP2-')],
            [sg.Text('', size=(120,2), key='-FEEDBACK-')],
            [sg.Image(convert_to_bytes(_fnames(imagepointer),resize=default_size,dirpath=source_folder),size=default_size,key='-IMAGE-')],
            [sg.Text((p := 'Change filename to:'),size=(len(p),1)),
             sg.InputText(fn := _fnames(imagepointer),size=(len(fn),1), key='-NEWFN-'),      
             sg.Submit('Rename'),
             sg.Text('',size=(len(fn),1), key='-NEWFNFEEDBACK-')],
            [sg.Button('Prev'), sg.Button('Next'), sg.Button('Delete',button_color=('#FFFFFF','#FF0000')),sg.Button('Quit')] ]

window = sg.Window('Image Sorter', layout, resizable=True,
             return_keyboard_events=True, use_default_focus=False)

of = tempfile.NamedTemporaryFile(prefix='fs-',
                                 suffix='.log',
                                 dir='/tmp')
while True:
  event, values = window.read()
  if (event == sg.WIN_CLOSED or event is None or
      event == 'Quit' or event.startswith('q')):
    break
  window['-FEEDBACK-'].update(value=f"Got event '{event}'")
  if str(event).startswith('Left:') or event == 'Prev':
    imagepointer = imagepointer-1 if imagepointer > 0 else len(fnames)-1
    window['-FEEDBACK-'].update(f'imagepointer is {imagepointer}')
    window['-NEWFN-'].update(_fnames(imagepointer))
    window['-TITLE-'].update(f"Simple image sorter: {_fnames(imagepointer)} [{imagepointer}/{len(fnames)}]")
    window['-IMAGE-'].update(data=convert_to_bytes(_fnames(imagepointer),resize=default_size,dirpath=source_folder),size=default_size)
    continue
  if str(event).startswith('Right:') or event == 'Next' or event == ' ' or event == 'image_clicked':
    imagepointer = imagepointer+1 if imagepointer < len(fnames)-1 else 0
    window['-FEEDBACK-'].update(f'imagepointer is {imagepointer}')
    window['-NEWFN-'].update(_fnames(imagepointer))
    window['-TITLE-'].update(f"Simple image sorter: {_fnames(imagepointer)} [{imagepointer}/{len(fnames)}]")
    window['-IMAGE-'].update(data=convert_to_bytes(_fnames(imagepointer),resize=default_size,dirpath=source_folder),size=default_size)
    continue

  source_filename = os.path.join(source_folder,fnames[imagepointer])

  if event == "Delete" or event == chr(63272):
    window['-FEEDBACK-'].update(value=f"You want to delete this")
    if os.path.exists(trashdir):
      pass
    else:
      try:
        os.mkdir(trashdir)
      except:
        window['-FEEDBACK-'].update(value=f"You want to delete this to {trashdir} but couldn't create")
        continue
    
    try:
      shutil.move(source_filename,trashdir)
    except BaseException as e:
      window['-FEEDBACK-'].update(value=f"deletion failed {e}")
      continue
    fnames.pop(imagepointer)
    window['-FEEDBACK-'].update(f'imagepointer is {imagepointer}')
    window['-NEWFN-'].update(_fnames(imagepointer))
    window['-TITLE-'].update(f"Simple image sorter: {_fnames(imagepointer)} [{imagepointer}/{len(fnames)}]")
    window['-IMAGE-'].update(data=convert_to_bytes(_fnames(imagepointer),resize=default_size,dirpath=source_folder),size=default_size)

  if event == 'Rename':
    new_target_filename = window['-NEWFN-']
    target_filename = os.path.join(target_dir, new_target_filename)
    new_target_fullpath = os.path.join(target_dir,new_target_filename)
    if os.path.exists(new_target_fullpath):
      window['-NEWFNFEEDBACK-'].update('Exists: ' + new_target_filename)
      window['-NEWFN-'].update(_fnames(imagepointer))
      continue
      
    if os.path.exists(target_filename):
      if os.path.getsize(target_filename) == os.path.getsize(source_filename):
        window['-FEEDBACK-'].update(value=f"{target_filename} already exists, same size as source")
      else:
        window['-FEEDBACK-'].update(value=f"{target_filename} already exists, different size as source")
      continue
      try:
        shutil.move(source_filename,new_target_filename)
      except BaseException as e: 
        window['-FEEDBACK-'].update(value=f"You want to rename this to {new_target_filename} but couldn't {e}")
        window['-NEWFN-'].update(_fnames(imagepointer))
        continue

      fnames[imagepointer] = new_target_filename
      window['-FEEDBACK-'].update(f'imagepointer is {imagepointer}')
      window['-NEWFN-'].update(_fnames(imagepointer))
      window['-TITLE-'].update(f"Simple image sorter: {_fnames(imagepointer)} [{imagepointer}/{len(fnames)}]")
      window['-IMAGE-'].update(data=convert_to_bytes(_fnames(imagepointer),resize=default_size,dirpath=source_folder),size=default_size)
    
  if event[0] in set_of_keys:
    target_dir = directory_for_key[event[0]]
    window['-FEEDBACK-'].update(value=f"You want to move this to {target_dir}")
    if not os.path.exists(target_dir):
      try:
        os.mkdir(target_dir)
      except:
        window['-FEEDBACK-'].update(value=f"Couldn't create dir {target_dir}")
        continue
    

    try:
      shutil.move((source_filename := os.path.join(source_folder,fnames[imagepointer])),directory_for_key[event[0]])
    except BaseException as e:
      print(f"exception {e} while moving to '{directory_for_key[event[0]]}")
      window['-FEEDBACK-'].update(value=f"exception {e} while moving to '{directory_for_key[event[0]]}")
      continue
    fnames.pop(imagepointer)
    window['-FEEDBACK-'].update(f'imagepointer is {imagepointer}')
    window['-TITLE-'].update(f"Simple image sorter: {_fnames(imagepointer)} [{imagepointer}/{len(fnames)}]")
    window['-NEWFN-'].update(_fnames(imagepointer))
    window['-IMAGE-'].update(data=convert_to_bytes(_fnames(imagepointer),resize=default_size,dirpath=source_folder),size=default_size)
