# The generation cap

If you run wall-film breakage in CFX and have never set this, your cascade is stopping after
three generations and nothing has told you.

```
pt real droplet breakup max generations = 3
```

An expert parameter, set in the solver, absent from the documentation.

## Why it binds

Every wall-film child is created as a **new particle**, one generation older than its parent. The
counter increments at every breakage event along a lineage. At the default the fourth generation
cannot be created, whatever energy the impact carries.

This is why the effect is invisible. Nothing errors. Nothing warns. The run completes, the
numbers are plausible, and they are low.

## How to tell whether it is binding on your case

Do not look for a warning, because there is not one. Reconstruct lineage instead: take every
impact, trace it back to the particle it came from, and count breakage events by generation.

What a bound cascade looks like:

| generation | impacts with enough energy to break | particles that broke |
|---:|---:|---:|
| 0 | many | many |
| 1 | many | many |
| 2 | many | many |
| 3 | **3,773** | **0** |

A model behaving oddly does not produce a clean zero against a large denominator. A gate does.

The denominator is the part that makes it conclusive. Showing that nothing broke at generation
three proves nothing on its own, because perhaps nothing should have. Showing that 3,773 impacts
carried more than enough energy and none of them broke is a different statement.

## What it costs

Box runs, four paired seeds per cap:

| | cap 3 (default) | cap 10 |
|---|---:|---:|
| Number-rate ratio against reference | 0.781 ± 0.025 | 1.020 ± 0.033 |

The effect is not uniform across modelling routes, and that asymmetry is what makes it dangerous
in a comparison:

| route | change in count when the cap is raised | why |
|---|---:|---|
| six children per impact | **+30.5%** | every child is a new particle, so the counter advances |
| one child per impact | **0.0%** | the child continues its parent's particle, so the counter never advances |
| re-injection | +31% recovered | children are launched as new particles through an injection region |

So a route compared against a wall film running at the default will appear to **over-count by
roughly 30%**, when what is actually happening is that the reference is under-counting. Two
routes that agree perfectly at cap 10 can look 30% apart at cap 3, with the discrepancy attributed
to the wrong one.

## What this document does not claim

That it is a bug. It may well be a deliberate guard against unbounded particle creation, which is
a real hazard: raising the cap to 10 increased parcels tracked by **4.3×** and peak particles in
flight by **2.6×** in the same box, and roughly tripled the wall clock.

What is measured, and all that is claimed, is that it is undocumented, that it silently truncates
breakage at a default value, that the truncation is invisible in the output, and that it affects
different modelling routes by different amounts.

Set it deliberately, whatever you set it to, and say which value you used when you report a
result.

## Checking the cost before you raise it

Raising the cap is not free. Before changing it, run the same case at both values and compare
parcels tracked, peak particles in flight, and wall clock, not just the quantity you care about.
In the box, going from 3 to 10 moved the quantity of interest by 39% and the cost by a factor of
four. A production case may not have that headroom, and the right answer may be to keep the cap
and report it rather than to raise it.
