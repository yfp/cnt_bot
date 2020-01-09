import numpy as np
import cv2

TILES_TOTAL = 280
TILE_WIDTH = 256

def concat_tile(im_list_2d):
    return cv2.vconcat([cv2.hconcat(im_list_h) for im_list_h in im_list_2d])

def random_tiling(tiles_shape, num_of_selected):
  size = tiles_shape[0]*tiles_shape[1]
  tile_ids = np.random.choice(TILES_TOTAL, size, replace=False)
  selected = np.random.choice(size, num_of_selected, replace=False)
  selected.sort()
  return tile_ids, selected

def repr_array(arr):
  return "-".join([str(n) for n in arr])

def repr_tile_ids_selected(tile_ids, selected):
  tile_str = repr_array(tile_ids)
  sel_str  = repr_array(selected)
  return f"{tile_str}__{sel_str}"

def from_repr(string):
  out = []
  for substr in string.split('__'):
    out.append( np.array([int(s) for s in substr.split('-')]) )
  return out

def guess_imagename(tile_ids):
  img_code = repr_array(tile_ids)
  return f"cache/g{img_code}.png"

def make_imagename(tile_ids, selected):
  img_code = repr_tile_ids_selected(tile_ids, selected)
  return f"cache/m{img_code}.png"

def generate_image(tile_ids, shape, selected=None):
  if selected is None:
    selected = tuple()

  tiles = [cv2.imread('tiles/cwt%03d.png' % n) for n in tile_ids]
  p1, p2 = 1, TILE_WIDTH-2
  # if len(selected) == 0:
  #   for i, tile in enumerate(tiles):
  #     cv2.putText(tile, str(i+1), (TILE_WIDTH-25,30),
  #                  cv2.FONT_HERSHEY_SIMPLEX,  
  #                1, (255,0,0), 2, cv2.LINE_AA)
  for i in selected:
      cv2.rectangle(tiles[i], (p1,p1), (p2,p2),
        color=(0,255,0), thickness=3)
  tiles = np.array(tiles).reshape(*shape,TILE_WIDTH,TILE_WIDTH,-1)
  image = concat_tile(tiles)
  if len(selected):
    fname = make_imagename(tile_ids, selected)
  else:
    fname = guess_imagename(tile_ids)
  cv2.imwrite(fname, image)
  return fname

if __name__ == '__main__':
  shape = (4,3)
  tile_ids, selected = random_tiling((4,3), 4)
  generate_image(tile_ids, shape, selected)
  generate_image(tile_ids, shape)