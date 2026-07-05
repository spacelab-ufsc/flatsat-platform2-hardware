#!/bin/bash
kicad-cli pcb render \
  --side top \
  --background transparent \
  --quality user \
  -D render.floor=false \
  -D render.shadows=false \
  -D render.postprocess=true \
  -w 15000 -h 10000 \
  -o top_pcb.png \
  ../sources/prototype.kicad_pcb

kicad-cli pcb render \
  --side bottom \
  --background transparent \
  --quality user \
  -D render.floor=false \
  -D render.shadows=false \
  -D render.postprocess=true \
  -w 15000 -h 10000 \
  -o bottom_pcb.png \
  ../sources/prototype.kicad_pcb
