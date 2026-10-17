# -*- coding: utf-8 -*-
"""Measure the fragment launch velocity and compare it with the prescribed answer.

    python check_repro.py repro_rotating_001

Standalone: needs only numpy.  Nothing from the sender's tooling is required, and no model has to be
reproduced - the routine hardcodes CPER = CPAR = 0.500, so in the frame of the wall every fragment
must leave with

    NCOR = 0.500,   TCOR = 0.500,   |v_out| / |v_in| = 0.500

A run directory may be given as "dir:omega" to measure a case at a different rotational speed; the
default is the 1500 rad/s of the supplied case.

Three things about the measurement are easy to get wrong and are handled explicitly:

 1. MEASURE ALONG THE LINEAGE, NOT ALONG ONE TRACK.  On a wall film wall a real impact ENDS the parent
    track and starts the children, so the pair to use is the parent's LAST record and the child's
    FIRST record.  A before/after on a single continuing track only ever samples near-misses.

 2. THE FIRST RECORD OF A TRACK IS WRITTEN ROTATED by Omega*t.  A child's birth point therefore only
    coincides with its parent's death point after rotating it back by -Omega*t.

 3. READ THE CHILD'S FIRST RECORD - the launch state.  After that the particle is integrated in the
    rotating frame, and at 1500 rad/s centrifugal and Coriolis terms move it by hundreds of m/s
    between records.

Track records are in the LAB frame, so the film wall's normal - (0,1,0) in the rotating frame, the
floor being flat - is turned by +Omega*t before the components are taken.
"""
import io, os, re, sys
import numpy as np

AX = np.array([0.0, 1.0, 1.0]) / np.sqrt(2.0)     # rotation axis, tilted off the wall normal
P0 = np.array([-0.065, 0.0, 0.0])                 # a point on the axis
OMG = 1500.0                                      # rad/s, matches DOMAIN MOTION in the CCL
FLOOR = -0.005                                    # y of the film wall
_INT, _FLT = re.compile(r"^-?\d+$"), re.compile(r"^[-+]?[\d.]+([eEdD][-+]?\d+)?$")


def read_trk(path):
    """Formatted CFX track file, 3 lines per record:
       [tid x y z t] / [dist d nrate u v] / [w T mass]."""
    rec, prev = [], []
    with io.open(path, encoding="latin-1") as fh:
        for line in fh:
            prev.append(line.split())
            if len(prev) > 3:
                prev.pop(0)
            if len(prev) == 3:
                a, b, c = prev
                if (len(a) == 5 and _INT.match(a[0]) and all(_FLT.match(q) for q in a[1:])
                        and len(b) == 5 and all(_FLT.match(q) for q in b)
                        and len(c) == 3 and all(_FLT.match(q) for q in c)):
                    rec.append((int(a[0]), float(a[1]), float(a[2]), float(a[3]), float(a[4]),
                                float(b[3]), float(b[4]), float(c[0])))
                    prev = []
    if not rec:
        raise SystemExit("no track records parsed from %s" % path)
    return np.array(rec)


def rot(V, ang, about_point):
    """Rodrigues rotation of each row of V by its own angle about AX (through P0 if about_point)."""
    d = V - P0 if about_point else V
    c, s = np.cos(ang)[:, None], np.sin(ang)[:, None]
    o = d * c + np.cross(AX, d) * s + AX * np.dot(d, AX)[:, None] * (1 - c)
    return o + P0 if about_point else o


def measure(run_dir, omg=OMG):
    """omg is the domain's angular velocity for THIS run. It must match the case: at omg = 0 the wall
    frame and the lab frame coincide, the wall velocity vanishes and the floor normal does not turn."""
    trk = os.path.join(run_dir, "PT1.trk")
    if not os.path.exists(trk):
        raise SystemExit("no PT1.trk in %s" % run_dir)
    R = read_trk(trk)
    tid = np.abs(R[:, 0]).astype(int)
    X, t, V = R[:, 1:4], R[:, 4], R[:, 5:8]
    o = np.lexsort((t, tid))
    tid, X, t, V = tid[o], X[o], t[o], V[o]
    first = np.ones(len(tid), bool); first[1:] = tid[1:] != tid[:-1]
    last = np.ones(len(tid), bool); last[:-1] = tid[1:] != tid[:-1]
    fi, li = np.flatnonzero(first), np.flatnonzero(last)
    b1 = fi[np.diff(np.append(fi, len(tid))) >= 2]
    if not len(b1):
        raise SystemExit("no candidate fragment tracks in %s" % run_dir)

    born = rot(X[b1], -omg * t[b1], True)
    rows = []
    for k, i in enumerate(b1):
        d = np.linalg.norm(X[li] - born[k], axis=1) + np.abs(t[li] - t[i]) * 2000.0
        # never pair a track with itself, and cope with there being no other track at all
        j = [q for q in np.argsort(d) if tid[li][q] != tid[i]]
        if not j:
            continue
        jj = j[0]
        if d[jj] > 1e-5:
            continue
        xlab, tlab = X[li][jj], t[li][jj]
        if abs(rot(xlab[None], np.array([-omg * tlab]), True)[0, 1] - FLOOR) > 2e-4:
            continue                                        # not a film-wall impact
        nlab = rot(np.array([[0.0, 1.0, 0.0]]), np.array([omg * tlab]), False)[0]
        U = omg * np.cross(AX, xlab - P0)                   # wall speed at the impact point
        win, wout = V[li][jj] - U, V[i] - U                 # into the frame of the wall
        an, bn = win.dot(nlab), wout.dot(nlab)
        ti, to = win - an * nlab, wout - bn * nlab
        rows.append((tid[li][jj], tid[i], abs(bn) / max(abs(an), 1e-12),
                     np.linalg.norm(to) / max(np.linalg.norm(ti), 1e-12),
                     np.linalg.norm(wout) / max(np.linalg.norm(win), 1e-12)))
    return rows


def main(dirs):
    print("wall film + rotating domain + breakage into two fragments")
    print("the routine hardcodes CPER = CPAR = 0.500, so every row below should read 0.500")
    print("=" * 84)
    for spec in dirs:
        d, _, om = spec.partition(":")
        omg = float(om) if om else OMG
        rows = measure(d, omg)
        print("\n%s   %d fragment(s)   [omega = %g rad/s]"
              % (os.path.basename(d.rstrip("/\\")), len(rows), omg))
        print("   %-8s %-8s %10s %10s %12s" % ("parent", "child", "NCOR", "TCOR", "speed ratio"))
        for p, c, ncor, tcor, sr in rows:
            flag = "" if max(abs(ncor - .5), abs(tcor - .5), abs(sr - .5)) < 0.02 else "   <-- WRONG"
            print("   %-8d %-8d %10.4f %10.4f %12.4f%s" % (p, c, ncor, tcor, sr, flag))
        if rows:
            a = np.array([r[2:] for r in rows])
            print("   %-17s %10.4f %10.4f %12.4f   (prescribed: 0.5000)"
                  % ("median", *np.median(a, axis=0)))


if __name__ == "__main__":
    main(sys.argv[1:] or ["repro_rotating_001"])
