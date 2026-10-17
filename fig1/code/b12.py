# compact cards: number + icon on the left, title and one line on the right
uses = [("advise", "Ask for advice", ["tools, parameters,", "strategies"]),
        ("code", "Ask for code", ["e.g. Python,", "Fiji macro"]),
        ("run", "Let an agent run it", ["runs and optimises", "the workflow"]),
        ("answer", "Ask for the answer", ["multimodal model,", "direct answer"])]
checks = [["Verify against the", "documentation or", "primary source"],
          ["Runs ≠ correct:", "test it on your", "reference images"],
          ["Limit what it can", "change; hold out", "reference data"],
          ["Validate against", "reference data before", "measuring anything"]]
CWu = (bw0 - 3 * 10) / 4
CH = 92
cyc = ly_ + lh_ + 46
bry = ly_ + lh_ + 23
xs_ = [bx0 + q * (CWu + 10) + CWu / 2 for q in range(4)]
b.append(f'<path d="M{xB+WB/2},{ly_+lh_} V{bry} M{xs_[0]},{bry} H{xs_[-1]}" fill="none" stroke="{kc}" stroke-width="2.4"/>')
gy = cyc + CH + 12
qy = gy + 28 + 14                 # check row
QH = 104
for q, (nm, ttl, sub) in enumerate(uses):
    cx_ = xs_[q]
    x0q = cx_ - CWu / 2
    b.append(arrow(cx_, bry, cx_, cyc - 3, kc, 2.4))
    b.append(group(f"LLM use {q+1}", rrect(x0q, cyc, CWu, CH, 10, k["tint"], k["tintstroke"], 1.3)
                   + f'<circle cx="{x0q+18}" cy="{cyc+18}" r="11" fill="{kc}"/>' + t(x0q + 18, cyc + 23, str(q + 1), 12.5, "bold", "#fff", "middle")
                   + ico(nm, x0q + 46, cyc + 56, kc)
                   + t(x0q + 86, cyc + 34, ttl, 16, "bold", "#6b2c87")
                   + t(x0q + 86, cyc + 56, sub, 13.5, fill=BODY, lh=16.5)))
    b.append(group(f"check {q+1}", rrect(x0q, qy, CWu, QH, 10, "#ffffff", k["tintstroke"], 1.3)
                   + check_badge(x0q + 26, qy + 30, kc, r=13).replace('stroke-width="4.5"', 'stroke-width="3"')
                   .replace(f"M{x0q+26-10},{qy+30+1} L{x0q+26-3},{qy+30+8} L{x0q+26+11},{qy+30-8}",
                            f"M{x0q+20},{qy+30} L{x0q+24.5},{qy+35} L{x0q+33},{qy+25}")
                   + t(x0q + 50, qy + 34, checks[q], 14, fill=INK, lh=19)))
gid = "llmgrad"
defs.append(f'<linearGradient id="{gid}" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#c7b3e0"/>'
            f'<stop offset="1" stop-color="{k["accent"]}"/></linearGradient>')
gx0, gx1 = xB + 14, xB + WB - 14
b.append(f'<path d="M{gx0},{gy} H{gx1-16} L{gx1},{gy+14} L{gx1-16},{gy+28} H{gx0} Z" fill="url(#{gid})"/>'
         + t(gx0 + 14, gy + 19, "more of the analysis delegated to the LLM  →  more decisions hidden", 15, "bold", "#ffffff"))
# keep: save the analysis, not the conversation (uses 1-3)
ky = qy + QH + 16
kh = YO + HTOP - 16 - ky
spl = xs_[3] - CWu / 2 - 5
b.append(rrect(bx0, ky, spl - bx0 - 5, kh, 10, "#ffffff", k["tintstroke"], 1.3))
b.append(t((bx0 + spl) / 2, ky + 24, "1–3: save the analysis, not the conversation", 15, "bold", INK, "middle"))
st_ = f'fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"'
iy = ky + 44 + (kh - 44) / 2 - 18          # icon centre
items = ["code / macro", "parameters, software", "LLM, version, date, step", "reruns without the LLM"]
xi = [bx0 + 30 + (spl - bx0 - 60) * (j + 0.5) / 4 for j in range(4)]
def doc(cx, cy):
    return f'<path d="M{cx-20},{cy-26} h28 l12,12 v40 h-40 z M{cx+8},{cy-26} v12 h12" {st_}/>'
ic = [doc(xi[0], iy) + f'<path d="M{xi[0]-6},{iy-4} l-7,7 l7,7 M{xi[0]+6},{iy-4} l7,7 l-7,7" {st_}/>',
      "".join(f'<line x1="{xi[1]-22}" y1="{iy-14+r*14}" x2="{xi[1]+22}" y2="{iy-14+r*14}" {st_}/>'
              f'<circle cx="{xi[1]-12+r*12}" cy="{iy-14+r*14}" r="5" fill="#fff" stroke="{INK}" stroke-width="2.4"/>' for r in range(3)),
      doc(xi[2], iy) + "".join(f'<line x1="{xi[2]-12}" y1="{iy-8+r*9}" x2="{xi[2]+12}" y2="{iy-8+r*9}" {st_}/>' for r in range(4)),
      check_badge(xi[3], iy, C["B"]["accent"] if "B" in C else kc, r=24)]
for j in range(4):
    b.append(group(f"keep {items[j]}", ic[j] + t(xi[j], iy + 50, items[j], 13.5, "bold" if j == 3 else "normal", INK if j == 3 else BODY, "middle")))
b.append(arrow(xi[2] + 34, iy, xi[3] - 32, iy, "#4a5568", 2.4))
# responsibility
ax_ = spl + 5
aw_ = bx0 + bw0 - ax_
b.append(rrect(ax_, ky, aw_, kh, 10, k["tint"], k["tintstroke"], 1.3))
px, py_ = ax_ + aw_ / 2, ky + 34 + (kh - 34) / 2 - 22
b.append(group("person", f'<circle cx="{px}" cy="{py_-12}" r="13" fill="none" stroke="{INK}" stroke-width="2.4"/>'
               f'<path d="M{px-24},{py_+30} a24,24 0 0 1 48,0" fill="none" stroke="{INK}" stroke-width="2.4"/>'))
b.append(t(px, py_ + 58, ["You remain", "responsible for", "every step"], 14.5, "bold", "#6b2c87", "middle", lh=18))
