import math
from .key import Key, KeyNode, Keyframe, KeyframeFlag, KeyFlag
from .tokenizer import Tokenizer
from .types import Vector3f


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _deg_to_rad(v):
    return math.radians(v)


def _expect_identifier(tok, expected):
    t = tok.getIdentifier()
    if t.upper() != expected.upper():
        raise AssertionError(f"Expected '{expected}', got '{t}'")


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

def _parse_header(tok, key: Key):
    _expect_identifier(tok, "FLAGS")
    key.flags = KeyFlag(tok.getIntNumber())

    _expect_identifier(tok, "TYPE")
    key.nodeTypes = tok.getIntNumber()

    _expect_identifier(tok, "FRAMES")
    key.numFrames = tok.getIntNumber()

    _expect_identifier(tok, "FPS")
    key.fps = tok.getFloatNumber()

    _expect_identifier(tok, "JOINTS")
    key.numJoints = tok.getIntNumber()


# ------------------------------------------------------------
# MARKERS (opcionais no Infernal Machine)
# ------------------------------------------------------------

def _parse_markers(tok, key: Key):
    _expect_identifier(tok, "MARKERS")
    count = tok.getIntNumber()

    markers = []
    for _ in range(count):
        time = tok.getFloatNumber()
        event = tok.getIntNumber()
        markers.append((time, event))

    key.markers = markers


# ------------------------------------------------------------
# KEYFRAME NODES
# ------------------------------------------------------------

def _parse_nodes(tok, key: Key):

    # Já consumimos "KEYFRAME" e "NODES" no load_key()

    _expect_identifier(tok, "NODES")
    num_nodes = tok.getIntNumber()

    for _ in range(num_nodes):
        _expect_identifier(tok, "NODE")
        idx = tok.getIntNumber()

        node = KeyNode()
        node.idx = idx

        _expect_identifier(tok, "MESH")
        _expect_identifier(tok, "NAME")
        node.meshName = tok.getIdentifier()

        _expect_identifier(tok, "ENTRIES")
        num_entries = tok.getIntNumber()

        frames = []

        for _e in range(num_entries):
            # número da entrada (ignorar)
            tok.getIntNumber()
            tok.assertPunctuator(':')

            frame = tok.getIntNumber()
            flags = tok.getIntNumber()

            x = tok.getFloatNumber()
            y = tok.getFloatNumber()
            z = tok.getFloatNumber()

            p = tok.getFloatNumber()
            yw = tok.getFloatNumber()
            r = tok.getFloatNumber()

            dx = tok.getFloatNumber()
            dy = tok.getFloatNumber()
            dz = tok.getFloatNumber()

            dp = tok.getFloatNumber()
            dyaw = tok.getFloatNumber()
            dr = tok.getFloatNumber()

            kf = Keyframe()
            kf.frame = frame
            kf.flags = KeyframeFlag(flags)
            kf.position = Vector3f(x, y, z)
            kf.orientation = Vector3f(p, yw, r)
            kf.deltaPosition = Vector3f(dx, dy, dz)
            kf.deltaRotation = Vector3f(dp, dyaw, dr)

            frames.append(kf)

        node.keyframes = frames
        key.nodes.append(node)


# ------------------------------------------------------------
# INTERPOLAÇÃO
# ------------------------------------------------------------

def _interpolate_frames(key: Key):
    total = key.numFrames

    for node in key.nodes:
        if not node.keyframes:
            continue

        kfs = sorted(node.keyframes, key=lambda k: k.frame)
        full = [None] * total

        # Colocar keyframes existentes
        for k in kfs:
            if 0 <= k.frame < total:
                full[k.frame] = k

        # Interpolar entre keyframes
        for i in range(len(kfs) - 1):
            k1 = kfs[i]
            k2 = kfs[i + 1]

            f1 = k1.frame
            f2 = k2.frame

            for f in range(f1 + 1, f2):
                alpha = (f - f1) / (f2 - f1)

                px = k1.position.x + (k2.position.x - k1.position.x) * alpha
                py = k1.position.y + (k2.position.y - k1.position.y) * alpha
                pz = k1.position.z + (k2.position.z - k1.position.z) * alpha

                rp = k1.orientation.x + (k2.orientation.x - k1.orientation.x) * alpha
                ry = k1.orientation.y + (k2.orientation.y - k1.orientation.y) * alpha
                rr = k1.orientation.z + (k2.orientation.z - k1.orientation.z) * alpha

                kf = Keyframe()
                kf.frame = f
                kf.flags = KeyframeFlag.AllChange
                kf.position = Vector3f(px, py, pz)
                kf.orientation = Vector3f(rp, ry, rr)
                full[f] = kf

        # Preencher antes do primeiro frame
        first = kfs[0]
        for f in range(0, first.frame):
            kf = Keyframe()
            kf.frame = f
            kf.flags = KeyframeFlag.AllChange
            kf.position = first.position
            kf.orientation = first.orientation
            full[f] = kf

        # Preencher depois do último frame
        last = kfs[-1]
        for f in range(last.frame + 1, total):
            kf = Keyframe()
            kf.frame = f
            kf.flags = KeyframeFlag.AllChange
            kf.position = last.position
            kf.orientation = last.orientation
            full[f] = kf

        # Converter ângulos para radianos
        for kf in full:
            kf.orientation = Vector3f(
                _deg_to_rad(kf.orientation.x),
                _deg_to_rad(kf.orientation.y),
                _deg_to_rad(kf.orientation.z),
            )

        node.keyframes = full


# ------------------------------------------------------------
# LOAD KEY (com MARKERS opcionais)
# ------------------------------------------------------------

def load_key(filepath):
    with open(filepath, "r", encoding="latin-1") as f:
        tok = Tokenizer(f)

        key = Key(filepath)

        # HEADER
        _expect_identifier(tok, "SECTION")
        tok.assertPunctuator(':')
        _expect_identifier(tok, "HEADER")
        _parse_header(tok, key)

        # Tentar ler SECTION: MARKERS ou SECTION: KEYFRAME
        _expect_identifier(tok, "SECTION")
        tok.assertPunctuator(':')

        next_id = tok.getIdentifier().upper()

        if next_id == "MARKERS":
            _parse_markers(tok, key)

            # Depois dos markers vem SECTION: KEYFRAME NODES
            _expect_identifier(tok, "SECTION")
            tok.assertPunctuator(':')
            _expect_identifier(tok, "KEYFRAME")
            _expect_identifier(tok, "NODES")

        elif next_id == "KEYFRAME":
            _expect_identifier(tok, "NODES")

        else:
            raise AssertionError(f"Expected MARKERS or KEYFRAME, got '{next_id}'")

        # KEYFRAME NODES
        _parse_nodes(tok, key)

        # Interpolar frames
        _interpolate_frames(key)

        return key