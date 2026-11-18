# Defects in ANSYS CFX wall-film breakage

A simulation disagreed with an experiment and nobody could say why. The cause was a frame
mismatch inside the solver, on a code path that had been in use for years. Tracking it down
turned up a second, unrelated defect: an undocumented parameter that silently stops a
fragmentation cascade after three generations, so every wall-film run at the default has been
under-counting fragments by about 30% without warning.

Neither defect crashes. Neither prints a warning. Both produce plausible numbers. A third, the same
frame problem in a second code path, is in section 3, and there the correction works.

Tested on **ANSYS CFX 2023 R2 (v232)**, Windows, Intel MPI. Earlier and later versions are
untested and the behaviour may differ.

## Vendor status, November 2026

**ANSYS Development reproduced the frame defect and corrected it in the solver.** The change is in
release **27R2**, which ANSYS says will be released in summer 2027. Support ticket 00630421.

Their description: in a rotating domain, child particles created at walls were given the wrong
**starting position** as well as the wrong velocity.

Two practical notes. The fix was described in terms of particles created at walls, so it may not
cover the second code path in section 3, the user-defined injection region, which reads the
velocity it is given in the lab frame. And section 2, the generation cap, is a separate finding
that nothing here says has changed.

If you are on 27R2 or later, section 1 should no longer apply, and I would be glad to hear whether
the reproducer here returns 0.5000 for you. On 2023 R2 and other earlier releases, the behaviour
below is what I measured.

Everything here runs in a synthetic box: a 10 mm gap, 100 µm particles, no real geometry. That
is deliberate. Every result below is reproducible by anyone with a CFX licence and none of it
depends on the application the work came from.

---

## 1. Restitution on a rotating wall is applied in the wrong frame

A particle user routine on a wall-film boundary is handed the impact velocity measured
**relative to the wall**. The velocity it returns for each child is then applied as though it
were **absolute**. On a stationary wall the two frames coincide and nothing is wrong, which is
why the path survived. On a wall that is moving, every fragment is launched short by the speed
of the wall.

### The reproducer

The way to make this undeniable is to remove the physics, so the right answer is known by
construction rather than by a model.

One particle. One impact. Two fragments. One timestep. A routine containing no breakage model
at all: no size distribution, no random draw. Both coefficients of restitution hardcoded at
**0.500**. Measured in the frame of the wall, each fragment must leave with a normal and a
tangential restitution of exactly 0.500.

| | prescribed | rotating | stationary control |
|---|---:|---:|---:|
| Normal restitution | 0.500 | **0.1066** | 0.5000 |
| Tangential restitution | 0.500 | **1.4640** | 0.5000 |
| Speed ratio, out over in | 0.500 | **0.5587** | 0.5000 |

The stationary control is the same case with the domain rotation removed, which is its only
difference. Both fragments are wrong identically. The tangential value exceeds 1, meaning the
fragment leaves the wall travelling along it faster than it arrived.

### Why the rotation axis is tilted

The box spins about (0, 1, 1)/√2 rather than about its floor normal. With a box spinning about
its own floor normal only the tangential coefficient comes out wrong and the normal one looks
perfect, which is how this can be missed. Tilting the axis puts 71% of the wall speed along the
film wall's normal and both coefficients are then affected. That is the situation on a real
rotor blade, whose surface normal is largely circumferential.

### What it is not

Each of these was eliminated by a test rather than by argument.

| Candidate cause | How it was ruled out | Result |
|---|---|---|
| The breakage model | There is no model in the routine; two fragments, coefficients hardcoded | no change |
| The wall normal | Film wall is the flat box floor, normal exactly (0,1,0), hardcoded in the routine | no change |
| Mesh or impact angle | The result is a ratio at a single impact, parent's last state to child's first | no change |
| The measurement | `check_repro.py` validated against a run whose answer was already known, reproduced to three decimals | no change |
| The routine itself | With rotation off, returns exactly 0.500 | no change |
| Run-to-run variation | Deterministic case; two independent builds and solves give identical numbers, two fragments agree to four decimals | no change |
| **Domain rotation** | **The only difference between the two cases** | **stripes the result** |

### The documentation is the argument

The vendor's page on *standard particle-wall interaction* states that a moving wall requires the
wall frame. Its page on the *user-defined wall film* path describes the child-velocity return
with no frame specified at all. The ambiguity is in the documentation, not only in the code.

**Status: reported to ANSYS in September 2026. Not adjudicated.** Nothing here should be read as
the vendor having confirmed a defect. The mechanism inside the solver is `[INFERRED]`, since the
source is closed; what is measured is the input, the output, and the one variable that changes
between them.

### A caveat before you apply the obvious repair

The algebraically consistent correction is to add the wall velocity back to the returned value.
In the box it is exact, through three chained impacts out to a wall-speed-to-impact-speed ratio
of 1.59.

It does not follow that it is deployable. In a full rotating machine the same correction
destabilises: impact counts explode and median impact speeds become unphysical. Those runs are
on geometry that is not published here, so no numbers are given for them. Whether the fault then
lies in the returned value or in the solver's own particle-wall separation test is not
observable from outside CFX, and that is the part still open with the vendor.

Treat the `+U` repair as a diagnostic that confirms the mechanism, not as a fix. The route in
section 3 avoids the affected code path instead.

---

## 2. An undocumented cap stops the cascade after three generations

This is the part most likely to affect other people, because it is on by default and nothing
reports it.

```
pt real droplet breakup max generations = 3
```

A hidden expert parameter. Every wall-film child is created as a new particle one generation
older than its parent, so at the default the cascade stops at the third generation regardless of
how much energy later impacts carry.

### How it was found

Not by reading the manual, because it is not in the manual. Every impact was traced back to the
particle it came from and then counted by generation. At generation three **no particle ever
broke, although 3,773 impacts carried more than enough energy to break one**. A model behaving
oddly does not produce a clean zero. A gate does.

### What it costs

Box runs, four paired seeds per cap:

| | cap 3 (default) | cap 10 |
|---|---:|---:|
| Number-rate ratio against reference | 0.781 ± 0.025 | 1.020 ± 0.033 |

Raising the cap moves the count of a six-children route by **+30.5%** and of a one-child route by
**0.0%**. The asymmetry is the explanation: a one-child fragment continues its parent's particle
and never increments the generation counter, so the cap never binds on it. A re-injection route
loses **31%** of its count at the default.

The consequence worth stating plainly: **any route compared against a wall film running at the
default appears to over-count by roughly 30%, when in fact the reference is under-counting.**
Published results that use the default are truncating fragmentation without saying so.

Whether this is a bug or an undocumented default is not for this repository to decide. What is
measured is that it is undocumented, that it silently stops breakage, and what it costs.

See [`docs/generation-cap.md`](docs/generation-cap.md).

---

## 3. The same frame problem in a second code path, and a fix that works

A user-defined injection region reads the velocity it is given in the **lab** frame, while the
wall routine is handed its velocity relative to the wall. The two paths disagree about frame in
opposite directions.

Here the correction does work. Hand CFX `v_wall-frame + Ω × r` and the launch is exact,
including the awkward case where the wall is moving into itself at twice the child's speed.

This is what makes a third modelling route possible: stop the parent at the wall and launch all
its children through an injection region one timestep later. That keeps the six children of the
wall-film route, avoids the frame defect of section 1 entirely, and is immune to the generation
cap of section 2, measured at **1413** fragments at cap 3 against **1407 ± 8** at cap 10 over
twelve seeds.

---

## 4. Which disagreements were real

Two routes to the same physics were compared in the box over multiple generations on two
walls. Some quantities agreed and one did not, and working out which of those was meaningful
took longer than finding either defect.

| Quantity | Ratio between routes | Verdict |
|---|---:|---|
| Mass flux | 1.0054 | agrees |
| Mass-weighted impact speed | 1.0000 | agrees |
| Mass-weighted impact angle | 1.0000 | agrees |
| Particle number rate | 2.5 to 3.6 | does not agree |

The second wall in the same run reproduces all of it to three digits, so none of this is a
one-surface artefact.

The number rate looks like the important disagreement. It turned out to be two things stacked on
top of each other, one a real defect and one not a disagreement at all, and separating them is
the useful part of this repository.

**It is not sampling noise.** That was the first explanation and it was wrong. Raising the parcel
count a hundredfold, from 10,355 to 1,052,945 impacts, leaves the ratio at 2.53. It wanders
between 2.4 and 2.8 with no trend towards 1. Monte-Carlo error falls as 1/√N, so a hundredfold
increase would have collapsed any genuine variance effect beyond recognition.

**Part of it was a real defect, in my own code rather than the solver's.** Each route carries a
small per-particle state payload in the unused low bits of the diameter, because the solver
carries one float per particle. One route attached that payload only when a particle broke, so a
particle that survived an impact was handed a fresh state at the next contact instead of keeping
the one it had. That is deterministic, which is why no parcel count ever closed it. Fixing the
branch removed most of the gap and left a residual of about 1.4. `DECISIONS.md` has the
instrumented measurement, and the explanation I had written down before taking it, which blamed
the solver and was wrong.

**The residual is a property of where you stop counting.** The number rate is dominated by the
smallest fragments, and the fragment cutoff that decides whether they are tracked is a modelling
choice rather than a physical quantity. Sweeping it in the reference route alone:

| fragment cutoff | reference number rate, relative to 2 µm | its own erosion |
|---|---:|---:|
| 1 µm | 3.93× | 1.0013 |
| 2 µm | 1.00× | 1.0000 |
| 4 µm | 0.27× | 0.9968 |

**Across that sweep the reference's own number rate moves by a factor of 14.4 while its own
erosion moves by 0.5%.** Repeating the sweep with the generation cap of section 2 corrected to
10 widens it to a factor of **22.0**, with mass flux and erosion still flat to within 2%. At a 2 µm cutoff, 75% of the reported number rate comes from the 1.3% of
mass below 3.5 µm. A quantity that unstable in the reference cannot settle an argument between
two routes, and chasing the ratio to 1.0 would have been chasing an artefact. Across the same
cutoff sweep the residual between routes moves from 1.785 to 1.348, which is the signature of a
disagreement that lives entirely in the fines the cutoff controls.

The box itself converges as expected, which is what justifies trusting the rest: ±22% at 634
parcels, ±6.5% at 6,298, ±2.3% at 63,279, consistent with 1/√parcels.

---

## Caveats

- **The vendor has confirmed nothing.** Both defects are reported, not adjudicated.
- **One CFX version.** 2023 R2 (v232). Version dependence is likely and untested.
- **The mechanism is inferred.** The source is closed. The measurements are not inferred; the
  explanation of what the solver is doing internally is.
- **The `+U` repair is not a fix.** See the caveat in section 1. Do not deploy it on the strength
  of the box result.
- **The box cannot speak about transport.** It runs with drag disabled, so every fragment follows
  its parent's path and transport is size-independent. That is what makes the box a clean test of
  the breakage operator and also what makes it silent on anything size-dependent downstream.
- **Erosion is not tested by the headline box case.** With normal injection and the restitution
  forced, every impact lands at 90°, where the ductile erosion proxy vanishes identically. The
  erosion agreement quoted above comes from the oblique configuration, not this one.
- **Written for one investigation, not as a general tool.** The routine is a diagnostic, not a
  library.

---

## What is here

```
src/pt_frag_wallframe.F   the child-velocity routine, no physical model, coefficients at 0.500
src/check_repro.py        the measurement; needs only numpy
docs/reproducer.md        how to build and run the two cases, and what to expect
docs/generation-cap.md    the cap, how it was found, and what it costs
docs/return-stack.md      the user-routine return layout, which is easy to get wrong
```

The solver input files are not included. A `.def` is only usable by someone who already has the
same CFX version, the compiler toolchain and the mesh, so for almost every reader it would be an
opaque binary rather than evidence. The measured numbers, the routine showing there is no model
in it, and the case specification in `docs/reproducer.md` are what make the claim checkable.

Dependencies: a CFX 2023 R2 licence and its compiler toolchain for the routine, numpy for the
measurement.
