# Decisions, and the things that turned out to be wrong

Kept during the investigation rather than written afterwards. It records what was tried, what
failed, and why each choice was made. Several entries are reversals of things stated confidently
earlier, and those are the entries worth reading.

---

## Build a reproducer with no model in it

The first version of the frame case used the real breakage routine. That was a mistake and it
cost about a week. Every anomaly could be answered with "your model is doing something odd", and
there was no way to settle it from outside.

Replacing the model with two fragments and two hardcoded coefficients made the correct answer
known by construction. The argument then needs no agreement about the physics: 0.500 was asked
for, 0.1066 came back, and the only thing that changed between the two runs was whether the
domain rotates.

**Rule taken from it:** when the question is whether the tool is wrong, the test case must have
an answer that does not depend on the tool.

---

## Tilt the rotation axis, deliberately

The earliest rotating case spun the box about its own floor normal. The tangential coefficient
came out wrong and the normal one looked perfect, which pointed at a tangential-only problem and
sent the search in the wrong direction for several runs.

Tilting the axis to (0, 1, 1)/√2 puts 71% of the wall speed along the film wall's normal, and
then both coefficients fail. One mechanism, two projections.

This also resolves an apparent contradiction with an earlier write-up of the same defect, which
reported the normal coefficient as exact. It was exact, for that geometry. The case is the
difference, not the finding.

---

## Eleven hypotheses, one test each

Listed before testing, so the list could not be trimmed to fit the answer afterwards. Six of
them are in the README table. The discipline that mattered was writing down what each test would
show if the hypothesis were true, before running it.

The one that did the most work was the stationary control, because it is the same case with one
block removed. Everything that survives in both cases is thereby excluded, without having to
reason about it individually.

---

## Retracted: the number-rate gap is the cascade compounding as 6^generation

**This was wrong.**

The two routes report particle number rates differing by a factor of about 3.5. The first
explanation was that the six-children route simply contains more breakage events, with the count
growing as 6 per generation.

The per-timestep data refutes it. A compounding effect keeps growing. This one plateaus:

| timestep | mass ratio | number-rate ratio |
|---:|---:|---:|
| 1 | 1.0167 | 2.165 |
| 2 | 1.0049 | 3.089 |
| 3 | 1.0046 | 3.647 |
| 4 | 1.0048 | 3.653 |
| 5 to 10 | 1.0045 to 1.0051 | 3.651 to 3.653 |

It rises over three steps and then sits at 3.653. That is a steady-state systematic factor, not
a divergence, so the compounding story cannot be the mechanism.

An observation that made it stranger and pointed somewhere useful: the reference population is
**finer** (d50 31.9 µm against 45.2 µm). Finer particles carry more number per unit mass, so the
reference should report the **higher** number rate. It reports the lower one. That is the
opposite sign to what its own size distribution implies, which is what ruled out a
population-composition effect and turned attention to how the two paths count.

---

## Retracted: the residual disagreement is sampling noise

**Also wrong, and this one was held for longer.**

The emission rule is provably unbiased per event, and an offline check reproduced it on 83,546
real events with a ratio of means of 1.0003. It was therefore natural to assume the run-level gap
was heavy-tailed variance that more parcels would smooth away.

The case was re-run at 1×, 3×, 10×, 30× and 100× parcels, comparing number rate per unit mass so
that parcel count divides out:

| parcels | floor impacts | ratio against reference |
|---|---:|---:|
| 1× | 10,355 | 2.799 |
| 3× | 31,700 | 2.510 |
| 10× | 105,385 | 2.375 |
| 30× | 315,070 | 2.507 |
| 100× | 1,052,945 | 2.529 |

A hundredfold increase leaves it at 2.53. Monte-Carlo error falls as 1/√N, so over 100× that is
a factor of ten in the error and it would have collapsed a genuine variance effect beyond
recognition.

**What it is instead** `[INFERRED]`: the two routes truncate the same divergent sum in different
places. Number rate scales as 1/d³, so a path that repeatedly draws the finest bin multiplies the
count enormously while its probability decays geometrically. One route enumerates every branch at
every generation and captures those paths deterministically; the other samples one path per
parcel and can only reach a depth set by the parcel count. No finite parcel count makes a sampled
version match an enumerated one. This is consistent with every measurement taken since but has
not been proved directly.

**Rule taken from it:** before concluding that a disagreement is noise, check that it moves in the
direction noise would move it. This one moved the wrong way.

---

## Test the advisor's proposal rather than argue about it

The proposal was to give the single daughter in the one-child route the number rate it would have
had as one of six fragments, rather than its parent's whole mass.

The per-size data showed the diagnosis behind it was exactly right. Parents match to 0.4%,
first-generation fragments are off by a factor of **6.006**, and the discrepancy compounds with
generation depth.

It still cannot be implemented as stated, and the reason is structural rather than a bug. The
solver's breakup factor is a single scalar N that sets both the child diameter, as N^(-1/3), and
the number rate multiplier. Mass is therefore conserved automatically for any N. Returning N/6 to
match the reference number rate also inflates the daughter's diameter by 6^(1/3) = 1.82, and the
only way to shed the rest of the mass is to absorb it into the wall.

Measured with that absorption applied:

| scheme | mass | per-fragment number rate | aggregate number rate |
|---|---|---|---|
| breakup factor as built | exact | 6× high | 2.8× high |
| factor plus absorption | **0.38×, destroyed** | **exact to 0.1%** | 2.7× low |

It reproduces the intended quantity to 0.1% and destroys 62% of the mass doing it. The aggregate
then overshoots to the other side, because a starved population never builds the fine-fragment
cascade at all.

**Decision: keep the existing scheme.** It is exact on mass and on erosion, and wrong only on a
number-weighted quantity that the README shows is not stable in the reference either. The
alternative breaks the half that works to half-fix the half that does not.

---

## Retracted: the solver was destroying my encoded payload

**Wrong, and I had blamed the solver for it in writing before checking.**

Both routes carry a small per-particle state payload in the unused low bits of the diameter,
because the solver carries one float per particle and the model needs a second number that
survives the track and the rank boundary. The payload here is the particle's fracture energy,
drawn once and never changed, so a particle that survives one impact at a given energy must
survive every later impact at the same energy.

One route was not behaving that way. Its particles kept breaking at energies they had already
survived.

The explanation I wrote down was that the solver recomputes the child diameter as
`d_parent * N^(-1/3)` when a breakup factor is returned, and that this arithmetic destroys the
encoded low bits.

**It does not.** Both routines were rebuilt with one added line recording whether a payload was
present at every wall interaction. Counting only records still at the parent size, meaning
particles that have never broken:

| route | records with a valid payload | without |
|---|---:|---:|
| six children | **60,385** | 24,697 |
| one child | **0** | 4,534 |

Payloads survive the round trip perfectly well. 61% of all wall interactions in the one-child
route decode a valid payload, and every fragment carries one. The only path that loses it is the
**no-break branch**, which leaves the diameter untouched and therefore attaches nothing. My own
branch, not the solver's arithmetic.

The consequence is that the route drew a fresh fracture energy at every contact, giving every
particle a new chance to break at each impact rather than locking in the survivors. That
deterministic difference, not any sampling effect, drove a large part of the population gap
between the two routes, which is why no parcel count ever closed it.

The fix is one branch: on the no-break path, return a breakup factor that reproduces the encoded
diameter, so the survivor carries its state forward exactly as the other route does.

**Rule taken from it:** the sentence "the tool is corrupting my data" needs an instrumented
measurement behind it, not an inference from downstream behaviour. The instrumented run took an
afternoon and the inference had already been written into two documents.

---

## Stop chasing the number-rate ratio to 1.0

Following from the two retractions above and the cutoff sweep. The reference's own number rate
moves by a factor of 14.4 across a cutoff change that moves its own erosion by 0.5%, rising to
22.0 once the generation cap is corrected.

Tuning one route to match another on a quantity that unstable in the reference would be fitting
to an artefact. The decision was to document the disagreement, state which quantities are
interchangeable and which are not, and stop.

| Trustworthy between routes | Not interchangeable |
|---|---|
| Mass flux | Particle counts |
| Erosion rate, and anything of the form mass × h(v, α) | Size-resolved distributions |

---

## Report to the vendor before publishing an explanation

The package sent in September 2026 asks which frame CFX expects, states what was measured, lists
what has been ruled out, and says a candidate explanation and a working change both exist and can
be shared.

It deliberately does not lead with the explanation. A report that opens with a diagnosis invites
a debate about the diagnosis; one that opens with a reproducible measurement and a narrow
question is harder to deflect, and leaves room for the answer to be "that is expected, here is
why".

As of this writing it is reported and not adjudicated, and the README says so.

**Update, November 2026.** ANSYS Development reproduced the frame defect and corrected it in
release 27R2. Their description is that in a rotating domain, child particles created at walls
were given the wrong starting position as well as the wrong velocity. The choice above is worth
recording as a result rather than a preference: the report opened with a reproducible measurement
and a narrow question rather than with a diagnosis, and it was answered with a code change.

---

## Do not ship the solver input files

They embed absolute paths from the machine they were built on, including directory names from the
project the work came from. Repacking a `.def` requires CFX itself, and byte-patching a solver
input that cannot then be validated is worse than not shipping it.

`docs/reproducer.md` carries the case specification instead, which is enough to rebuild it and is
also more useful than an opaque binary.
