"""Generate the pixel-art desktop icon (job-lister.ico) on a 64x64 grid."""
from PIL import Image

SIZE = 64

BG = (0xF4, 0xEF, 0xE3, 255)
K = (0x1B, 0x20, 0x30, 255)
HAIR = (0xC8, 0x81, 0x3A, 255)
HAIR_L = (0xE3, 0xA8, 0x62, 255)
HAIR_D = (0xA3, 0x63, 0x2A, 255)
SKIN = (0xF6, 0xCB, 0xA3, 255)
SKIN_D = (0xE2, 0xAC, 0x83, 255)
MOUTH = (0x9C, 0x6A, 0x50, 255)
SUIT = (0x9A, 0xA1, 0xAB, 255)
SUIT_L = (0xB8, 0xBF, 0xC8, 255)
SUIT_D = (0x74, 0x7B, 0x86, 255)
SHIRT = (0xF4, 0xF6, 0xF8, 255)
TIE = (0xCF, 0x3B, 0x3B, 255)
TIE_D = (0xA5, 0x2C, 0x2C, 255)
SHOE = (0x2A, 0x2F, 0x3C, 255)

CORNER = [7, 5, 3, 2, 2, 1, 1]  # pixels clipped per row from each edge


def build():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def box(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px[x, y] = c

    # ---- head ------------------------------------------------------------
    face_rows = {9: (25, 38), 10: (24, 39), 23: (24, 39), 24: (25, 38)}
    for y in range(9, 25):
        x0, x1 = face_rows.get(y, (23, 40))
        box(x0, y, x1, y, SKIN)
    box(21, 16, 22, 19, SKIN)   # ears
    box(41, 16, 42, 19, SKIN)
    box(21, 17, 21, 18, SKIN_D)
    box(42, 17, 42, 18, SKIN_D)

    # hair: dome over the top, sideburns down past the ears, swept fringe
    hair_rows = {6: (27, 36), 7: (25, 38), 8: (24, 39), 9: (23, 40)}
    for y in range(6, 14):
        x0, x1 = hair_rows.get(y, (22, 41))
        box(x0, y, x1, y, HAIR)
    box(22, 14, 30, 14, HAIR)   # fringe sweeping to one side
    box(22, 15, 25, 15, HAIR)
    box(22, 14, 23, 18, HAIR)   # sideburns
    box(40, 14, 41, 18, HAIR)
    box(26, 7, 32, 8, HAIR_L)   # highlight
    box(25, 9, 29, 9, HAIR_L)
    box(24, 13, 39, 13, HAIR_D)  # shadow under the fringe
    box(26, 14, 30, 14, HAIR_D)

    # ---- face details ----------------------------------------------------
    box(26, 15, 29, 15, HAIR_D)  # brows
    box(34, 15, 37, 15, HAIR_D)
    box(27, 17, 28, 18, K)       # eyes
    box(35, 17, 36, 18, K)
    box(31, 19, 32, 20, SKIN_D)  # nose
    box(29, 22, 34, 22, MOUTH)   # mouth
    box(23, 20, 23, 23, SKIN_D)  # cheek shading
    box(40, 20, 40, 23, SKIN_D)

    # ---- neck ------------------------------------------------------------
    box(29, 25, 34, 26, SKIN)
    box(29, 25, 34, 25, SKIN_D)

    # ---- jacket ----------------------------------------------------------
    box(22, 27, 41, 27, SUIT)
    box(19, 28, 44, 28, SUIT)
    box(18, 29, 45, 43, SUIT)     # sleeves + torso
    box(24, 44, 39, 45, SUIT)     # torso continues past the cuffs
    box(18, 29, 19, 43, SUIT_D)   # shading on the outer sleeves
    box(44, 29, 45, 43, SUIT_D)
    box(23, 30, 23, 45, K)        # sleeve separation
    box(40, 30, 40, 45, K)

    # shirt V with the tie over it, both narrowing toward the waist
    for y in range(28, 42):
        half = 4 - (y - 28) // 4
        half = max(1, half)
        left, right = 32 - half, 31 + half
        box(left, y, right, y, SHIRT)
        px[left - 1, y] = K       # lapel edges
        px[right + 1, y] = K
        px[left - 2, y] = SUIT_L
        px[right + 2, y] = SUIT_L
        if y >= 30:
            t0, t1 = (left + 1, right - 1) if right - left >= 3 else (left, right)
            box(t0, y, t1, y, TIE)
            box(t1, y, t1, y, TIE_D)
    box(30, 28, 33, 29, TIE)      # knot
    box(33, 28, 33, 29, TIE_D)
    box(31, 42, 32, 43, TIE)      # tip
    box(32, 45, 32, 45, SUIT_D)   # button

    # cuffs + hands
    box(18, 43, 22, 43, K)
    box(41, 43, 45, 43, K)
    box(18, 44, 22, 46, SKIN)
    box(41, 44, 45, 46, SKIN)
    box(19, 47, 21, 47, SKIN)
    box(42, 47, 44, 47, SKIN)
    box(18, 44, 18, 46, SKIN_D)
    box(45, 44, 45, 46, SKIN_D)
    box(24, 45, 39, 45, K)        # jacket hem

    # ---- legs + shoes ----------------------------------------------------
    box(26, 46, 30, 58, SUIT)
    box(33, 46, 37, 58, SUIT)
    box(30, 46, 30, 58, SUIT_D)
    box(33, 46, 33, 58, SUIT_D)
    box(24, 59, 30, 61, SHOE)
    box(33, 59, 39, 61, SHOE)

    return img


def outline(img):
    px = img.load()
    out = img.copy()
    opx = out.load()
    for y in range(SIZE):
        for x in range(SIZE):
            if px[x, y][3]:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < SIZE and 0 <= ny < SIZE and px[nx, ny][3]:
                    opx[x, y] = K
                    break
    return out


def add_background(img):
    px = img.load()
    for y in range(SIZE):
        edge = min(y, SIZE - 1 - y)
        clip = CORNER[edge] if edge < len(CORNER) else 0
        for x in range(SIZE):
            if px[x, y][3] == 0:
                px[x, y] = BG if clip <= x < SIZE - clip else (0, 0, 0, 0)
    return img


if __name__ == "__main__":
    base = add_background(outline(build()))
    base.resize((256, 256), Image.NEAREST).save("icon_preview.png")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [
        base.resize((s, s), Image.NEAREST if s % SIZE == 0 else Image.LANCZOS)
        for s in sizes
    ]
    frames[-1].save("job-lister.ico", append_images=frames[:-1],
                    sizes=[(s, s) for s in sizes])
    print("wrote job-lister.ico + icon_preview.png")
