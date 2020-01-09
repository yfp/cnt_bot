import numpy as np
from telegram import ReplyKeyboardMarkup

imsets = []
freqs = []
imset_dict = {}

class Imset:  
  def __init__(self, obj):
    self.shape = tuple(obj['shape'])
    self.nos = obj['num_of_selected']
    self.name = "{}/{}".format(self.nos, self.shape[0]*self.shape[1])

def load_imsets(config):
  global imsets, freqs, imset_dict
  for obj in config.imsets:
    imset = Imset(obj)
    imsets.append(imset)
    freqs.append(obj['freq'])
    imset_dict[imset.name] = imset

    size = obj['shape'][0]*obj['shape'][1]
    arr = (1+np.arange(size).reshape(obj['shape'])).tolist()
    arr = [[str(i) for i in l] for l in arr]
    config.keyboard[imset.name] = ReplyKeyboardMarkup(arr, resize_keyboard=True)

    print(f"Registered imset `{imset.name}` = {imset.shape[0]}×{imset.shape[1]} at {obj['freq']}")
  freqs = np.array(freqs)
  freqs = freqs/freqs.sum()

def get_imset(name=None):
  if name in imset_dict:
    return imset_dict[name]
  return np.random.choice(imsets, p=freqs)