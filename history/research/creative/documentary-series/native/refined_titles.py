"""Readable period hierarchy and a clear Taswira link; accepted identity retained."""
from pathlib import Path
import sys
from PIL import Image
P=Path('/home/user/taswira/master-polish-2026-11-03');sys.path.insert(0,str(P))
from master_titles import Titles,old
W,H=1080,1920
class RefinedTitles(Titles):
 def intro(self,t,bg):
  # Retain a visible kingdom silhouette from frame one beneath the clearing fog.
  fog=self.bg.fog(bg,t);im=Image.blend(bg.convert('RGB'),fog.convert('RGB'),.66).convert('RGBA')
  strength=old.ease((t-.4)/.5)*(1-old.ease((t-6.1)/.6))
  im.alpha_composite(Image.new('RGBA',(W,H),(0,0,0,round(64*strength))))
  self.emblem_at(im,t,.45,3.45,width=205,cy=455)
  self.wind(im,'HAUSA KINGDOM CHRONICLES',675,24,t,.65,3.45,'sora',600,4)
  self.wind(im,'ANCIENT',815,66,t,.75,3.45,'serif',500,8)
  self.wind(im,'KANO',965,214,t,.9,3.45,'serif',500,14)
  self.simple(im,'KANO, HAUSALAND',1165,36,t,1.9,6.0,600,2)
  self.simple(im,'11th–15th centuries CE',1235,55,t,2.05,6.0,500)
  self.simple(im,'First walls c. 1095–1134',1315,40,t,2.2,6.0,500)
  self.simple(im,'Rumfa · 1463–1499',1375,40,t,2.3,6.0,500)
  self.simple(im,'CINEMATIC REIMAGINING',1450,25,t,2.4,6.0,600,2)
  self.simple(im,'Early dates follow the Kano Chronicle',1495,24,t,2.45,6.0,450)
  return im.convert('RGB')
 def frame(self,t,background=None):
  im=super().frame(t,background).convert('RGBA')
  # All existing production/music/source credits retain their readable positions.
  self.simple(im,'EXPLORE THE MAP · TASWIRA',1365,29,t,15.0,19.35,650,1.5)
  return im.convert('RGB')
