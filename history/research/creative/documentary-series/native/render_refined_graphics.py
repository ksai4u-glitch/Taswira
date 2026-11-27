"""Render native typography components separately; never overwrites delivery."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
p=Path('/home/user/taswira/cinematic-rebuild');P=Path('/home/user/taswira/master-polish-2026-11-03')
sys.path.insert(0,str(p));sys.path.insert(0,str(P))
from master_renderer import Reader,encoder,finish
from refined_titles import RefinedTitles
kind=sys.argv[1];g=RefinedTitles();g.bg.type=lambda *args,**kwargs:None
if kind=='intro':
 dec=Reader('/home/user/taswira/full-city-test/taswira-city-flight-23s-review.mp4',duration=8.5);nframes=204
else:
 dec=Reader(P/'palace-labelled-plus-pullback.mp4',start=9.5,duration=2);nframes=480
enc=encoder(p/('native-cinematic-'+kind+'.mp4'))
for n in range(nframes):
 t=n/24
 if kind=='intro':im=g.intro(t,Image.fromarray(dec.frame()))
 else:im=g.frame(t,Image.fromarray(dec.frame()) if n<48 else None)
 enc.stdin.write(np.array(im).tobytes())
 if n%48==0:print('NATIVE_GRAPHICS_FRAME',kind,n,flush=True)
dec.close();finish(enc);print('NATIVE_GRAPHICS_COMPLETE',kind,flush=True)
