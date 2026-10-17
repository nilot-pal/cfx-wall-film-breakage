# Rebuilding the frame reproducer

The two solver input files are not shipped, for the reason given at the end of `DECISIONS.md`.
This is the specification they were built from.

## The case

A rectangular box with a wall film on the floor. The domain rotates at **1500 rad/s** about the
axis **(0, 1, 1)/√2**, which is tilted away from the floor normal on purpose: see the note in the
README on why a box spinning about its own floor normal hides half the effect.

- A single **100 µm** particle, injected from a point by a standard CCL cone injection, with no
  injection routine involved.
- Injection velocity **(20, −100, 0) m/s**, so it strikes the film wall once.
- **One timestep.** The particle user routine on the film wall returns two fragments and nothing
  else.
- The floor is flat, so the film wall normal is exactly **(0, 1, 0)** in the rotating frame and
  is hardcoded in the routine. No Additional Variables are involved.
- Expert parameter `pt real droplet breakup max children = 2`.

The **stationary control** is the identical case with the domain rotation removed. That means
deleting the `DOMAIN MOTION` block and the `Frame Type = Rotating` on the walls that follows from
it. Nothing else changes.

## Running it

Compile the routine:

```
cfx5mkext -name pt_frag_wallframe -dest <libdir> ../src/pt_frag_wallframe.F
```

`cfx5mkext` needs the compiler on `PATH` **and** `LIB` set. Without `LIB` the compile succeeds and
the link fails on `ifconsol.lib`, which is a confusing way to fail.

Point the case at your library directory:

```
cfx5cmds -read  -definition repro_rotating.def -text c.ccl
# edit the Library Path line in c.ccl
cfx5cmds -write -definition repro_rotating.def -text c.ccl
```

Solve both, then measure:

```
cfx5solve -def repro_rotating.def   -name repro_rotating   -batch
cfx5solve -def repro_stationary.def -name repro_stationary -batch
python ../src/check_repro.py repro_rotating_001 repro_stationary_001:0
```

The `:0` gives the stationary run its angular velocity of zero. `check_repro.py` needs only
numpy.

Each run's `.out` should report `Entered domain : 1` and `New child droplets created : 2`. If it
does not, the case is not doing what this document describes and the numbers below will not mean
anything.

## What you should see

| | prescribed | rotating | stationary |
|---|---:|---:|---:|
| Normal restitution | 0.500 | 0.1066 | 0.5000 |
| Tangential restitution | 0.500 | 1.4640 | 0.5000 |
| Speed ratio | 0.500 | 0.5587 | 0.5000 |

Both fragments should agree with each other to four decimals. The case is deterministic, so two
independent builds give identical numbers.

## How the measurement works

Three things here are easy to get wrong, and `check_repro.py` handles each explicitly. They are
worth knowing even if you never run this case, because they apply to any wall-film measurement.

**1. Measure along the lineage, not along one track.** On a wall-film wall a real impact *ends*
the parent track and *starts* the children. The pair to compare is the parent's last record and
the child's first record. A before-and-after on a single continuing track only ever samples
near-misses, which is why an early version of this measurement saw nothing wrong.

**2. The first record of a track is written rotated by Ω·t.** A child's birth point only
coincides with its parent's death point after rotating it back by −Ω·t.

**3. Read the child's first record, which is the launch state.** After that the particle is
integrated in the rotating frame, and at 1500 rad/s the centrifugal and Coriolis terms move it by
hundreds of m/s between successive records. Reading the second record gives a number that has
nothing to do with restitution.

Track records are in the **lab** frame, so the film wall normal, exactly (0, 1, 0) in the
rotating frame, must be turned by +Ω·t before components are taken.
