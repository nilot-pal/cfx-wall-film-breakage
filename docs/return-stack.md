# The user-routine return stack

Notes on the wall-film child-droplet return layout for CFX 2023 R2 (v232), written down because
three things in it are easy to get wrong and none of them fails loudly.

With `pt real droplet breakup max children = NCH`, the return stack is `NRET = 7 * NCH`.

| Block | Slots |
|---|---|
| Child Droplet Breakup Indicator | `RET(1, 1 .. NCH)` |
| Child Droplet Diameter | `RET(1, NCH+1 .. 2*NCH)` |
| Child Droplet Number Rate | `RET(1, 2*NCH+1 .. 3*NCH)` |
| Child Droplet Velocity | `RET(1, 3*NCH+1 .. 6*NCH)` |
| Child Droplet Mode | `RET(1, 6*NCH+1 .. 7*NCH)` |

For `NCH = 2` that is `NRET = 14`, with the velocity block at `RET(1, 7..12)`.

The argument list is Velocity, Mean Particle Diameter, Particle Number Rate, Particle Position,
so `NARG = 8`.

## The three traps

**1. The velocity block is child-major.** Child *i* owns

```
RET(1, 3*NCH + 3*(i-1) + 1  ..  3*NCH + 3*(i-1) + 3)
```

Writing it child-minor, which is the natural guess, puts one child's *v* component into the next
child's *u*. The run completes and the fragments fly off in wrong directions, with no error.

**2. Child mode must be 1.** That is `__regular_particle__`. A child written with mode 0 never
launches. It does not warn; the child simply is not there, and the only symptom is a fragment
count lower than you asked for.

**3. The velocity you return is read in a different frame from the one you were given.** This is
the defect in section 1 of the README. The impact velocity handed to the routine is measured
relative to the wall; what you return is applied as though it were absolute. On a stationary wall
these coincide. On a moving wall they do not, and nothing in the documentation for this path
specifies which frame is expected.

## Checking your own return stack

Set both restitution coefficients to a constant, return two fragments, and run a single impact on
a **stationary** wall. You should get exactly what you prescribed. If you do not, the problem is
in the layout above and not in your physics, and it is worth fixing before anything else is
trusted.

Then repeat on a rotating wall. If the numbers change, you are looking at the frame issue rather
than at your model.
