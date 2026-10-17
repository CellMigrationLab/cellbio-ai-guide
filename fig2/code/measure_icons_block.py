cuts = [0]
ms = []
# counts
for (dx, dy) in [(-22, -14), (4, -22), (24, -2), (-14, 10), (10, 18), (-34, 14), (32, 22)]:
    ms.append(f'<circle cx="{117+dx}" cy="{660+dy}" r="13" fill="#9cc3ee" stroke="{cA["accent"]}" stroke-width="2"/>'
              f'<circle cx="{117+dx}" cy="{660+dy}" r="5.5" fill="{cA["accent"]}"/>')
ms.append(t(117, 726, "Counts", 15.5, fill=INK, anchor="middle"))
cuts.append(len(ms))
# morphology: three cell shapes with different features (spiky / elongated / protrusive)
mcol, mfill = cA["accent"], "#9cc3ee"
spikes = []
for k in range(13):
    ang = 2 * math.pi * k / 13 + 0.2
    ln = 22 + (5 if k % 2 else 0)
    spikes.append(f'<line x1="{214+13*math.cos(ang):.1f}" y1="{666+13*math.sin(ang):.1f}" x2="{214+ln*math.cos(ang):.1f}" '
                  f'y2="{666+ln*math.sin(ang):.1f}" stroke="{mcol}" stroke-width="2" stroke-linecap="round"/>')
ms.append('<g inkscape:label="cell spiky (filopodia)">' + "".join(spikes)
          + f'<circle cx="214" cy="666" r="14" fill="{mfill}" stroke="{mcol}" stroke-width="2.2"/>'
          + f'<circle cx="214" cy="666" r="6" fill="{mcol}"/></g>')
ms.append(f'<g inkscape:label="cell elongated" transform="translate(262 660) rotate(-58)">'
          f'<path d="M-36,0 C-18,-11 18,-11 36,0 C18,11 -18,11 -36,0 Z" fill="{mfill}" stroke="{mcol}" stroke-width="2.2" '
          f'stroke-linejoin="round"/><ellipse cx="0" cy="0" rx="9" ry="5" fill="{mcol}"/></g>')
# protrusive cell: round body with a thin, ruffled lamellipodium fanning out to the upper right
lam = ["M3,-11"]
angs = [math.radians(a) for a in range(-80, 51, 13)]
for i, ang in enumerate(angs):
    r_out = 31 if i % 2 == 0 else 27
    lam.append(f"Q{(r_out+5)*math.cos(ang - 0.11):.1f},{(r_out+5)*math.sin(ang - 0.11):.1f} "
               f"{r_out*math.cos(ang):.1f},{r_out*math.sin(ang):.1f}")
lam.append("L8,9 Z")
ms.append(f'<g inkscape:label="cell protrusive (lamellipodium)" transform="translate(296 676)">'
          f'<path d="{" ".join(lam)}" fill="#cfe2f6" stroke="{mcol}" stroke-width="1.8" stroke-linejoin="round"/>'
          f'<circle cx="0" cy="0" r="13" fill="{mfill}" stroke="{mcol}" stroke-width="2.2"/>'
          f'<circle cx="-1" cy="1" r="6" fill="{mcol}"/></g>')
ms.append(t(263, 726, "Morphology", 15.5, fill=INK, anchor="middle"))
cuts.append(len(ms))
# phenotypes
for (dx, dy, colr) in [(-26, -16, "#2ec4b6"), (0, -26, "#ff7a3d"), (24, -12, "#7b5cff"), (-14, 6, "#ff4fa3"),
                       (12, 10, "#2f9a43"), (-32, 20, "#ffd23f"), (30, 20, "#3ec1ff"), (0, 30, "#c86bff")]:
    ms.append(f'<circle cx="{409+dx}" cy="{662+dy}" r="9.5" fill="{colr}"/>')
ms.append(t(409, 726, "Phenotypes", 15.5, fill=INK, anchor="middle"))
cuts.append(len(ms))
# tracks
for i, colr in enumerate(["#2f9a43", "#d6336c", "#7b5cff", "#1f6fc5"]):
    rr = random.Random(40 + i)
    px, py = 498, 694 - i * 18
    pts = [(px, py)]
    for _ in range(5):
        px += rr.uniform(18, 24)
        py += rr.uniform(-16, 6)
        pts.append((px, py))
    ms.append(f'<polyline points="{" ".join(f"{p:.1f},{q:.1f}" for p, q in pts)}" fill="none" stroke="{colr}" stroke-width="2.4"/>')
    ms += [f'<circle cx="{p:.1f}" cy="{q:.1f}" r="3.2" fill="{colr}"/>' for p, q in pts]
ms.append(t(555, 726, ["Tracks", "and dynamics"], 15.5, fill=INK, anchor="middle", lh=19))
cuts.append(len(ms))
old_c = [(117, 662), (263, 664), (409, 664), (555, 662)]
for i in range(4):
    cx, cy = POS[i]
    a.append(f'<g transform="translate({cx:.1f} {cy}) scale(0.9) translate({-old_c[i][0]} {-old_c[i][1]})">'
             + group(f"icon {MEAS[i][0]}", "".join(ms[cuts[i]:cuts[i + 1] - 1])) + "</g>")
    a.append(t(cx, cy + 58, MEAS[i][0], 16, "bold", INK, "middle") + t(cx, cy + 78, MEAS[i][1], 14, fill=BODY, anchor="middle"))
