import json,sys,html
d=json.load(open(sys.argv[1])); els=[e for e in d["elements"] if not e.get("isDeleted")]
P=40
xs=[e["x"] for e in els]+[e["x"]+e["width"] for e in els]
ys=[e["y"] for e in els]+[e["y"]+e["height"] for e in els]
minx,miny,maxx,maxy=min(xs)-P,min(ys)-P,max(xs)+P,max(ys)+P
W,H=maxx-minx,maxy-miny
BG=d.get("appState",{}).get("viewBackgroundColor","#ffffff")
o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
   f'<rect width="{W:.0f}" height="{H:.0f}" fill="{BG}"/>']
def X(v): return v-minx
def Y(v): return v-miny
for e in els:
    t=e["type"]; sc=e["strokeColor"]; bg=e.get("backgroundColor","transparent")
    dash=' stroke-dasharray="8 5"' if e.get("strokeStyle")=="dashed" else ""
    if t=="rectangle":
        fill=bg if bg!="transparent" else "none"
        o.append(f'<rect x="{X(e["x"]):.1f}" y="{Y(e["y"]):.1f}" width="{e["width"]:.1f}" height="{e["height"]:.1f}" rx="10" fill="{fill}" stroke="{sc}" stroke-width="{e["strokeWidth"]}"{dash}/>')
    elif t=="line":
        pts=" ".join(f'{X(e["x"])+p[0]:.1f},{Y(e["y"])+p[1]:.1f}' for p in e["points"])
        o.append(f'<polyline points="{pts}" fill="none" stroke="{sc}" stroke-width="{e["strokeWidth"]}"{dash}/>')
    elif t=="text":
        fs=e["fontSize"]; lh=fs*e.get("lineHeight",1.25)
        lines=e["text"].split("\n")
        y0=Y(e["y"])+fs*0.92
        o.append(f'<text x="{X(e["x"]):.1f}" y="{y0:.1f}" fill="{sc}" font-size="{fs}" xml:space="preserve">')
        for i,ln in enumerate(lines):
            dy=0 if i==0 else lh
            o.append(f'<tspan x="{X(e["x"]):.1f}" dy="{dy:.1f}">{html.escape(ln)}</tspan>')
        o.append('</text>')
o.append('</svg>')
open(sys.argv[2],"w").write("\n".join(o))
print("svg:",int(W),"x",int(H))
